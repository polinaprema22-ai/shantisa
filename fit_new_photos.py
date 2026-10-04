#!/usr/bin/env python3
"""Студийные снимки 2:3 → кадр карточки 9:16 без потери фигуры.

Если фигура с полями помещается в окно 9:16 по всей высоте снимка — обрезаем бока.
Если нет (платье в полный рост, локти у краёв) — достраиваем фон сверху/снизу
цветом крайних строк, только с той стороны, где фигура не упирается в край.

Запуск: ~/.local/imgtools/bin/python fit_new_photos.py SRC.png DST.jpg [SRC DST ...]
"""
import sys
import numpy as np
from PIL import Image, ImageFilter
from rembg import remove, new_session

ASPECT = 9 / 16
SIDE = 0.04   # запас по бокам от ширины снимка
session = new_session("u2net")


def bbox(mask):
    ys, xs = np.where(np.asarray(mask) > 128)
    return xs.min(), ys.min(), xs.max(), ys.max()


def trim_frame(im, limit=10):
    """Срезать тонкую белую рамку по краям (снимки пришли скриншотами)."""
    a = np.asarray(im).astype(np.float32).mean(axis=2)
    h, w = a.shape
    t = 0
    while t < limit and a[t].mean() >= 245: t += 1
    b = 0
    while b < limit and a[h - 1 - b].mean() >= 245: b += 1
    l = 0
    while l < limit and a[:, l].mean() >= 245: l += 1
    r = 0
    while r < limit and a[:, w - 1 - r].mean() >= 245: r += 1
    return im.crop((l, t, w - r, h - b))


def band(im, rows, top):
    """Полоса фона: цвет крайних строк по столбцам, размытый по горизонтали."""
    w, h = im.size
    a = np.asarray(im).astype(np.float32)
    edge = a[2:12] if top else a[-12:-2]
    col = np.median(edge, axis=0)                      # (w, 3)
    b = np.repeat(col[None, :, :], rows, axis=0).astype(np.uint8)
    return Image.fromarray(b).filter(ImageFilter.GaussianBlur(12))


def fit(src, dst):
    im = trim_frame(Image.open(src).convert("RGB"))
    w, h = im.size
    mask = remove(im, session=session, only_mask=True)
    x0, y0, x1, y1 = bbox(mask)
    cw = round(h * ASPECT)
    need = (x1 - x0) + 2 * SIDE * w
    closeup = x0 <= 2 or x1 >= w - 3                    # ткань во весь кадр — достраивать нечего
    if need <= cw or closeup:                          # помещается или крупный план — режем бока
        cx = (x0 + x1) / 2
        left = int(min(max(0, cx - cw / 2), w - cw))
        out = im.crop((left, 0, left + cw, h))
        how = "crop"
    else:                                              # не помещается — достраиваем фон
        H = round(w / ASPECT)
        add = H - h
        if add <= 0:                                   # снимок уже не шире рамки — только подрезать по высоте
            y = (h - H) // 2
            out = im.crop((0, y, w, y + H))
            out.save(dst, quality=90, optimize=True, progressive=True)
            print(dst.split("/")[-1], "trim", out.size)
            return
        touch_top, touch_bot = y0 <= 2, y1 >= h - 3
        if touch_bot and not touch_top:
            top, bot = add, 0
        elif touch_top and not touch_bot:
            top, bot = 0, add
        else:
            top = add // 2; bot = add - top
        out = Image.new("RGB", (w, H))
        if top: out.paste(band(im, top, True), (0, 0))
        out.paste(im, (0, top))
        if bot: out.paste(band(im, bot, False), (0, top + h))
        F = 14
        for i in range(F):                             # растушёвка шва
            k = (i + 1) / (F + 1)
            if top:
                y = top + i
                out.paste(Image.blend(out.crop((0, top - 1, w, top)), out.crop((0, y, w, y + 1)), k), (0, y))
            if bot:
                y = top + h - 1 - i
                out.paste(Image.blend(out.crop((0, top + h, w, top + h + 1)), out.crop((0, y, w, y + 1)), k), (0, y))
        how = "pad top=%d bottom=%d" % (top, bot)
    out.save(dst, quality=90, optimize=True, progressive=True)
    print(dst.split("/")[-1], how, out.size)


if __name__ == "__main__":
    args = sys.argv[1:]
    for s, d in zip(args[::2], args[1::2]):
        fit(s, d)
