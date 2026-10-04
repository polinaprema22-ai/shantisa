#!/usr/bin/env python3
"""Снимки уже 9:16 (вырезки из коллажа): срезать края коллажа, затем
крупный план — обрезать по высоте, вещь целиком — достроить фон по бокам.

Запуск: ~/.local/imgtools/bin/python fit_narrow.py SRC DST l,t,r,b closeup|full
(l,t,r,b — сколько пикселей срезать с каждого края)
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

ASPECT = 9 / 16


def side_band(im, cols, left):
    a = np.asarray(im).astype(np.float32)
    edge = a[:, 2:12] if left else a[:, -12:-2]
    col = np.median(edge, axis=1)                      # (h, 3)
    b = np.repeat(col[:, None, :], cols, axis=1).astype(np.uint8)
    return Image.fromarray(b).filter(ImageFilter.GaussianBlur(12))


def fit(src, dst, cut, mode):
    l, t, r, b = map(int, cut.split(","))
    im = Image.open(src).convert("RGB")
    w, h = im.size
    im = im.crop((l, t, w - r, h - b)); w, h = im.size
    if w / h > ASPECT:                                 # шире рамки — режем бока
        cw = round(h * ASPECT); x = (w - cw) // 2
        out = im.crop((x, 0, x + cw, h))
    elif mode == "closeup":                            # уже рамки, ткань — режем по высоте
        ch = round(w / ASPECT); y = (h - ch) // 2
        out = im.crop((0, y, w, y + ch))
    else:                                              # уже рамки, вещь целиком — достраиваем бока
        W = round(h * ASPECT); add = W - w; lp = add // 2; rp = add - lp
        out = Image.new("RGB", (W, h))
        out.paste(side_band(im, lp, True), (0, 0)); out.paste(im, (lp, 0))
        out.paste(side_band(im, rp, False), (lp + w, 0))
        F = 12
        for i in range(F):                             # растушёвка швов
            k = (i + 1) / (F + 1)
            out.paste(Image.blend(out.crop((lp - 1, 0, lp, h)), out.crop((lp + i, 0, lp + i + 1, h)), k), (lp + i, 0))
            x = lp + w - 1 - i
            out.paste(Image.blend(out.crop((lp + w, 0, lp + w + 1, h)), out.crop((x, 0, x + 1, h)), k), (x, 0))
    if out.height > 800:
        out = out.resize((round(out.width * 780 / out.height), 780), Image.LANCZOS)
    out.save(dst, quality=90, optimize=True, progressive=True)
    print(dst.split("/")[-1], out.size)


if __name__ == "__main__":
    fit(*sys.argv[1:5])
