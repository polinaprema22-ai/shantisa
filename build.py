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

    OUT.write_text("window.PRODUCTS = " + json.dumps(items, ensure_ascii=False, indent=1) + ";\n",
                   encoding="utf-8")
    sold = sum(i["status"] == "sold" for i in items)
    print("Товаров: %d (продано %d) → %s" % (len(items), sold, OUT.relative_to(ROOT)))
    if problems:
        print("\nПроверить:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)


if __name__ == "__main__":
    main()
