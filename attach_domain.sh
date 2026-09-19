#!/bin/zsh
# Привязать shantisa.ru к GitHub Pages. Запускать, когда домен уже резолвится в адреса GitHub.
set -e
cd "$(dirname "$0")"
T=$(grep '^GITHUB_TOKEN_POLINA=' ~/.claude/secrets/tokens.env | cut -d= -f2)
echo "shantisa.ru" > docs/CNAME
./publish.sh
sleep 60
curl -s -m 30 -X PUT -H "Authorization: Bearer $T" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/polinaprema22-ai/shantisa/pages -d '{"cname":"shantisa.ru"}' -o /dev/null -w "cname set: %{http_code}\n"
# ждём сертификат и включаем HTTPS
for i in $(seq 1 30); do
  st=$(curl -s -m 30 -H "Authorization: Bearer $T" https://api.github.com/repos/polinaprema22-ai/shantisa/pages | python3 -c "import sys,json; print(json.load(sys.stdin).get('https_certificate',{}).get('state'))")
  echo "cert: $st"; [ "$st" = "approved" ] && break; sleep 30
done
curl -s -m 30 -X PUT -H "Authorization: Bearer $T" -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/polinaprema22-ai/shantisa/pages -d '{"cname":"shantisa.ru","https_enforced":true}' -o /dev/null -w "https enforced: %{http_code}\n"
curl -s -o /dev/null -m 30 -w "https://shantisa.ru → %{http_code}\n" -L https://shantisa.ru/
