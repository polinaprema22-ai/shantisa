#!/usr/bin/env python3
"""Дописать проверенный кадр Codex в конец галереи карточки, не трогая остальные фото.

  ~/.local/imgtools/bin/python append_codex.py SH-31 back
"""
import csv, os, sys
import numpy as np
from PIL import Image
sys.argv, args = sys.argv[:1], sys.argv[1:]
ROOT = os.path.dirname(os.path.abspath(__file__)); os.chdir(ROOT); sys.path.insert(0, ROOT)
import fit_new_photos as fn
sid, view = args
rows = list(csv.DictReader(open("products.csv", encoding="utf-8-sig"))); fields = list(rows[0].keys())
model = next(r["model"] or r["id"] for r in rows if r["id"] == sid)
photos = next(r["photos"] for r in rows if (r["model"] or r["id"]) == model).split("|")
out = "raw/codex/%s/fit-%s.jpg" % (model, view)
fn.fit("raw/codex/%s/%s.png" % (model, view), out)
im = Image.open(out).convert("RGB")
if im.height > 1100:
    im = im.resize((round(im.width * 1100 / im.height), 1100), Image.LANCZOS)
a = np.asarray(im.convert("L")).astype(float)
assert min(a[:, :2].mean(), a[:, -2:].mean(), a[:2].mean(), a[-2:].mean()) > 60, "тёмный край"
n = max(int(p.rsplit("-", 1)[1].split(".")[0]) for p in photos) + 1
name = "%s-%d.jpg" % (model, n)
im.save("docs/photos/" + name, quality=90, optimize=True, progressive=True)
for r in rows:
    if (r["model"] or r["id"]) == model:
        r["photos"] = "|".join(photos + [name])
w = csv.DictWriter(open("products.csv", "w", encoding="utf-8", newline=""), fieldnames=fields); w.writeheader(); w.writerows(rows)
print(model, "→", photos + [name])
