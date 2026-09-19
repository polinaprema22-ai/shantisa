#!/usr/bin/env python3
"""Для вещей в пол ставит первым фото кадр, где фигура видна целиком (по raw/tg/photo_stats.json).

Переставляет файлы docs/photos/<ID>-k.jpg и колонку photos в products.csv. Запуск после process_photos.py.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent
PH = ROOT / "docs" / "photos"
stats = json.loads((ROOT / "raw/tg/photo_stats.json").read_text())
rows = list(csv.DictReader(open(ROOT / "products.csv", encoding="utf-8")))

for r in rows:
    names = [n for n in r["photos"].split("|") if n]
    if not names or "в пол" not in r["name"].lower():
        continue
    full = [n for n in names if stats.get(n, {}).get("full")]
    if not full:
        continue
    cover = max(full, key=lambda n: stats[n]["fig_h"])
    if cover == names[0]:
        continue
    order = [cover] + [n for n in names if n != cover]
    tmp = [(n, PH / (n + ".tmp")) for n in order]
    for n, t in tmp:
        (PH / n).rename(t)
    for k, (n, t) in enumerate(tmp, 1):
        t.rename(PH / ("%s-%d.jpg" % (r["id"], k)))
    print(r["id"], "обложка ←", cover)

w = csv.DictWriter(open(ROOT / "products.csv", "w", newline="", encoding="utf-8"), fieldnames=rows[0].keys())
w.writeheader(); w.writerows(rows)
