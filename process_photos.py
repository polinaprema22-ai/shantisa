#!/usr/bin/env python3
"""Обработка фото каталога: найти фигуру, обрезать пустое место, выправить свет.

Запуск (нужен venv с rembg): ~/.local/imgtools/bin/python process_photos.py [--bg] [ID ...]
  без аргументов — все фото из raw/tg по mapping.tsv → docs/photos
  --bg          — дополнительно заменить фон на чистый студийный (docs/photos-bg)
Оригиналы не трогаются: источник raw/tg/photos, результат docs/photos.
"""
import csv
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from rembg import new_session, remove

ROOT = Path(__file__).parent
RAW = ROOT / "raw" / "tg" / "photos"
OUT = ROOT / "docs" / "photos"
OUT_BG = ROOT / "docs" / "photos-bg"
ASPECT = 9 / 16          # рамка карточки: вертикальная, платье в пол помещается целиком
MARGIN = (0.05, 0.03, 0.06)   # сверху, снизу, по бокам — доля от высоты/ширины фигуры
BG_TOP, BG_BOTTOM = (246, 240, 242), (226, 214, 222)   # студийный фон: светло-пудровый градиент

session = new_session("u2net")


def figure_box(mask):
    """Прямоугольник фигуры по маске (alpha > 100)."""
    bw = mask.point(lambda a: 255 if a > 100 else 0)
    return bw.getbbox()


def crop_window(size, box):
    """Окно кадра с полями вокруг фигуры, растянутое до ASPECT в пределах снимка."""
    w, h = size
    x0, y0, x1, y1 = box
    fh, fw = y1 - y0, x1 - x0
    y0 = max(0, y0 - fh * MARGIN[0]); y1 = min(h, y1 + fh * MARGIN[1])
    x0 = max(0, x0 - fw * MARGIN[2]); x1 = min(w, x1 + fw * MARGIN[2])
    cw, ch = x1 - x0, y1 - y0
    if cw / ch < ASPECT:          # слишком узко — добираем ширину
        need = ch * ASPECT
        x0 = max(0, min(x0 - (need - cw) / 2, w - need)); x1 = min(w, x0 + need)
    else:                          # слишком широко — добираем высоту, сначала вниз (ноги), потом вверх
        need = cw / ASPECT
        extra = need - ch
        y1 = min(h, y1 + extra * 0.6); y0 = max(0, y0 - (need - (y1 - y0)))
        y1 = min(h, y0 + need)
    return tuple(int(round(v)) for v in (x0, y0, x1, y1))


def white_balance(im, mask):
    """Фон (где маска пустая) считаем нейтрально-серым и выравниваем каналы."""
    bg = mask.point(lambda a: 255 if a < 40 else 0)
    if bg.getbbox() is None:
        return im
    means = [ch.crop(bg.getbbox()) for ch in im.split()]
    from PIL import ImageStat
    r, g, b = (ImageStat.Stat(ch, bg).mean[0] for ch in im.split())
    m = (r + g + b) / 3
    gains = [min(1.45, max(0.75, m / c)) for c in (r, g, b)]
    return Image.merge("RGB", [ch.point(lambda v, k=k: min(255, int(v * k))) for ch, k in zip(im.split(), gains)])


def strip_bars(im):
    """Срезать чёрные полосы сверху/снизу (кадры из видео)."""
    g = im.convert("L"); w, h = im.size
    rows = [sum(g.getpixel((x, y)) for x in range(0, w, 8)) / len(range(0, w, 8)) for y in range(h)]
    top = next((y for y in range(h) if rows[y] > 18), 0)
    bot = next((y for y in range(h - 1, -1, -1) if rows[y] > 18), h - 1)
    return im.crop((0, top + 2, w, bot - 1)) if (top > 4 or bot < h - 5) else im


def enhance(im):
    im = ImageOps.autocontrast(im, cutoff=(0.3, 0.1))
    im = ImageEnhance.Brightness(im).enhance(1.04)
    im = ImageEnhance.Color(im).enhance(1.06)
    return im.filter(ImageFilter.UnsharpMask(radius=1.5, percent=80, threshold=2))


def studio_bg(cut):
    """Вырезанная фигура на пудровом градиенте."""
    w, h = cut.size
    bg = Image.new("RGB", (w, h))
    px = bg.load()
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOTTOM))
        for x in range(w):
            px[x, y] = col
    bg.paste(cut, (0, 0), cut)
    return bg


def process(src, dst, dst_bg=None):
    im = strip_bars(Image.open(src).convert("RGB"))
    cut = remove(im, session=session)          # RGBA: фигура с прозрачным фоном
    mask = cut.split()[3]
    box = figure_box(mask)
    if box is None:
        box = (0, 0) + im.size
    win = crop_window(im.size, box)
    out = enhance(white_balance(im.crop(win), mask.crop(win)))
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst, quality=90)
    if dst_bg:
        cut_c = cut.crop(win)
        # мягкий край маски, чтобы волосы не были «вырезаны ножницами»
        a = cut_c.split()[3].filter(ImageFilter.GaussianBlur(1.2))
        cut_c.putalpha(a)
        fig = enhance(Image.merge("RGB", cut_c.split()[:3]))
        fig.putalpha(a)
        dst_bg.parent.mkdir(parents=True, exist_ok=True)
        studio_bg(fig).save(dst_bg, quality=90)
    return {"win": win, "fig_h": (box[3] - box[1]) / im.size[1], "full": box[3] < im.size[1] - 6 and box[1] > 6}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    with_bg = "--bg" in sys.argv
    rows = list(csv.DictReader(open(ROOT / "products.csv", encoding="utf-8")))
    mapping = {l.split("\t")[0]: l.split("\t")[1].split() for l in open(ROOT / "raw/tg/mapping.tsv").read().splitlines() if "\t" in l}
    import json
    stats_path = ROOT / "raw/tg/photo_stats.json"
    stats = json.loads(stats_path.read_text()) if stats_path.exists() else {}
    for r in rows:
        if args and r["id"] not in args:
            continue
        for k, stem in enumerate(mapping.get(r["id"], []), 1):
            name = "%s-%d.jpg" % (r["id"], k)
            stats[name] = process(RAW / (stem + ".jpg"), OUT / name, (OUT_BG / name) if with_bg else None)
            print(name, stats[name]["win"], "full" if stats[name]["full"] else "", flush=True)
            stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=0))


if __name__ == "__main__":
    main()
