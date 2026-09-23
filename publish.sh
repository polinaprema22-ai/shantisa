#!/bin/zsh
# Пересобрать каталог из products.csv и выложить на GitHub Pages.
# Запуск: ~/shantisa-sale/publish.sh  (после правок в products.csv — например, статус «продано»)
set -e
cd "$(dirname "$0")"
python3 build.py
T=$(grep '^GITHUB_TOKEN_POLINA=' ~/.claude/secrets/tokens.env | cut -d= -f2)
git add -A
git -c commit.gpgsign=false commit -q -m "Обновление каталога $(date '+%d.%m.%Y %H:%M')" || { echo "Изменений нет"; exit 0; }
git push -q "https://x-access-token:$T@github.com/polinaprema22-ai/shantisa.git" main
echo "Опубликовано: https://shantisa.ru/ (обновится через 1–2 минуты)"
