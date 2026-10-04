#!/usr/bin/env python3
"""Поставить проверенные кадры Codex в карточку.

  ~/.local/imgtools/bin/python install_codex.py SH-42 model front back side 34
Порядок аргументов = порядок фото в галерее (первый — обложка).
Берёт raw/codex/SH-xx/<вид>.png, вписывает в 9:16 (fit_new_photos), кладёт docs/photos/SH-xx-N.jpg,
старые фото карточки уносит в raw/replaced-2026-10-04, обновляет photos во всех строках этой модели.
"""
import csv, os, sys, shutil
import numpy as np
from PIL import Image
sys.argv, args = sys.argv[:1], sys.argv[1:]
ROOT = os.path.dirname(os.path.abspath(__file__)); os.chdir(ROOT); sys.path.insert(0, ROOT)
import fit_new_photos as fn
sid, views = args[0], args[1:]
rows = list(csv.DictReader(open("products.csv", encoding="utf-8-sig"))); fields = list(rows[0].keys())
model = next(r["model"] or r["id"] for r in rows if r["id"] == sid)
for r in rows:
    if (r["model"] or r["id"]) == model:
        for p in r["photos"].split("|"):
            if p and os.path.exists("docs/photos/" + p):
                shutil.move("docs/photos/" + p, "raw/replaced-2026-10-04/%s-pre-codex.jpg" % p[:-4])
names = []
for k, v in enumerate(views, 1):
    out = "raw/codex/%s/fit-%s.jpg" % (model, v)
    fn.fit("raw/codex/%s/%s.png" % (model, v), out)
    im = Image.open(out).convert("RGB")
    if im.height > 1100:
        im = im.resize((round(im.width * 1100 / im.height), 1100), Image.LANCZOS)
    a = np.asarray(im.convert("L")).astype(float)
    assert min(a[:, :2].mean(), a[:, -2:].mean(), a[:2].mean(), a[-2:].mean()) > 60, "тёмный край у " + out
    name = "%s-%d.jpg" % (model, k)
    im.save("docs/photos/" + name, quality=90, optimize=True, progressive=True)
    names.append(name)
for r in rows:
    if (r["model"] or r["id"]) == model:
        r["photos"] = "|".join(names)
w = csv.DictWriter(open("products.csv", "w", encoding="utf-8", newline=""), fieldnames=fields); w.writeheader(); w.writerows(rows)
print(model, "→", names)
