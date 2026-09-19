#!/usr/bin/env python3
"""PDF-шпаргалка для менеджера: фото + артикул + имя + описание + размеры + цена. A4, без браузера (PIL)."""
import csv, json
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).parent
W, H = 2480, 3508                      # A4 при 300 dpi
M, COLS, ROWS = 120, 3, 3
F = "/System/Library/Fonts/Supplemental/"
def font(name, size):
    for cand in (name, "Arial.ttf"):
        try: return ImageFont.truetype(F + cand, size)
        except OSError: pass
    return ImageFont.load_default()
f_id, f_name, f_desc, f_small, f_h = font("Arial Bold.ttf", 44), font("Georgia.ttf", 60), font("Arial.ttf", 36), font("Arial.ttf", 34), font("Georgia.ttf", 72)

items = json.loads(open(ROOT / "docs/products.js", encoding="utf-8").read().split("=", 1)[1].rstrip().rstrip(";"))
cw, ch = (W - 2 * M) // COLS, (H - 2 * M - 160) // ROWS
pages = []
for pi in range(0, len(items), COLS * ROWS):
    page = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(page)
    d.text((M, 60), "Архив Shantisa — каталог для менеджера", font=f_h, fill="#141414")
    d.text((W - M - 420, 80), "стр. %d / %d" % (len(pages) + 1, -(-len(items) // (COLS * ROWS))), font=f_small, fill="#767676")
    for k, it in enumerate(items[pi:pi + COLS * ROWS]):
        x, y = M + (k % COLS) * cw, M + 160 + (k // COLS) * ch
        ph = int(ch * 0.62)
        im = Image.open(ROOT / "docs" / it["photos"][0]).convert("RGB")
        im.thumbnail((cw - 40, ph)); page.paste(im, (x + (cw - 40 - im.width) // 2 + 20, y))
        ty = y + ph + 24
        d.rectangle([x + 20, ty, x + 20 + 230, ty + 60], fill="#E40146"); d.text((x + 34, ty + 8), it["id"], font=f_id, fill="white")
        d.text((x + 270, ty - 4), "%s руб." % format(it["price"], ",").replace(",", " "), font=f_name, fill="#141414")
        d.text((x + 20, ty + 76), "«%s»" % it["title"], font=f_name, fill="#141414")
        # описание в 2 строки
        words, lines, cur = it["name"].split(), [], ""
        for w_ in words:
            if d.textlength(cur + " " + w_, font=f_desc) > cw - 40: lines.append(cur); cur = w_
            else: cur = (cur + " " + w_).strip()
        lines.append(cur)
        for i, ln in enumerate(lines[:2]): d.text((x + 20, ty + 150 + i * 44), ln, font=f_desc, fill="#4a4a4a")
        sizes = ", ".join("%s (%s)" % (v["size"], v["id"]) if len(it["variants"]) > 1 else v["size"] for v in it["variants"])
        d.text((x + 20, ty + 250), "Размер: " + sizes, font=f_small, fill="#141414")
        d.text((x + 20, ty + 296), it["color"], font=f_small, fill="#767676")
    pages.append(page)
out = ROOT / "каталог-для-менеджера.pdf"
pages[0].save(out, save_all=True, append_images=pages[1:], resolution=300)
print(out, len(pages), "страниц")
