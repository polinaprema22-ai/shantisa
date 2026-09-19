#!/usr/bin/env python3
"""products.csv → docs/products.js. Проверяет, что все фото на месте.

Запуск: python3 build.py
Колонка photos — имена файлов из docs/photos через «|», первое — обложка.
Статус: «в наличии» / «бронь» / «продано».
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "products.csv"
SITE = ROOT / "docs"
OUT = SITE / "products.js"

STATUS = {"в наличии": "available", "бронь": "reserved", "продано": "sold"}


def num(value):
    value = (value or "").strip().replace(" ", "")
    return int(value) if value.isdigit() else None


def main():
    items, problems = [], []
    with SRC.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            pid = (row.get("id") or "").strip()
            if not pid:
                continue
            status = STATUS.get((row.get("status") or "").strip().lower())
            if not status:
                problems.append("%s: неизвестный статус «%s»" % (pid, row.get("status")))
                status = "available"
            photos = [p.strip() for p in (row.get("photos") or "").split("|") if p.strip()]
            for p in photos:
                if not (SITE / "photos" / p).exists():
                    problems.append("%s: нет файла photos/%s" % (pid, p))
            if not photos:
                problems.append("%s: нет ни одного фото" % pid)
            items.append({
                "id": pid,
                "model": (row.get("model") or "").strip(),
                "category": (row.get("category") or "").strip(),
                "name": row["name"].strip(),
                "color": row["color"].strip(),
                "size": row["size"].strip().upper(),
                "fabric": row["fabric"].strip(),
                "measures": {k: num(row.get(k)) for k in ("bust", "waist", "hips", "length")},
                "condition": row["condition"].strip(),
                "price": num(row["price"]),
                "old_price": num(row.get("old_price")),
                "photos": ["photos/" + p for p in photos],
                "status": status,
                "note": (row.get("note") or "").strip(),
            })

    # Одна модель в нескольких размерах (одинаковый `model`) — одна карточка с вариантами
    groups = {}
    for it in items:
        key = it.pop("model") or it["id"]
        g = groups.setdefault(key, {**{k: v for k, v in it.items() if k not in ("size", "status")},
                                    "id": key, "variants": []})
        g["variants"].append({"id": it["id"], "size": it["size"], "status": it["status"]})
        if not g["photos"] and it["photos"]:
            g["photos"] = it["photos"]
    grouped = list(groups.values())
    for g in grouped:
        st = {v["status"] for v in g["variants"]}
        g["status"] = "available" if "available" in st else "reserved" if "reserved" in st else "sold"
    OUT.write_text("window.PRODUCTS = " + json.dumps(grouped, ensure_ascii=False, indent=1) + ";\n",
                   encoding="utf-8")
    sold = sum(i["status"] == "sold" for i in items)
    print("Вещей: %d (продано %d), карточек: %d → %s" % (len(items), sold, len(grouped), OUT.relative_to(ROOT)))
    if problems:
        print("\nПроверить:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)


if __name__ == "__main__":
    main()
