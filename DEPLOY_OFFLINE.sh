#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP=".mikrobot_before_offline_$STAMP"
mkdir -p "$BACKUP" static
for f in app.py index.html requirements.txt knowledge.json; do
  [ -f "$f" ] && cp -f "$f" "$BACKUP/" || true
done
[ -d static ] && cp -a static "$BACKUP/static-old" 2>/dev/null || true

python3 -m pip install -q -r requirements.txt
cp -f app.py "$PWD/app.py"
cp -f static/index.html "$PWD/static/index.html"
cp -f static/manifest.webmanifest "$PWD/static/manifest.webmanifest"
cp -f static/sw.js "$PWD/static/sw.js"
cp -f knowledge.json "$PWD/knowledge.json"
touch static/favicon.ico
python3 -m py_compile app.py
pkill -f 'uvicorn.*8765' 2>/dev/null || true
fuser -k 8765/tcp 2>/dev/null || true
sleep 2
nohup env PORT=8765 python3 -m uvicorn app:app --host 0.0.0.0 --port 8765 --workers 1 > mikrobot.log 2>&1 &
sleep 4
curl -fsS http://127.0.0.1:8765/api/health
echo
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8765/
echo "MIKROBOT OFFLINE PRO ONLINE"
