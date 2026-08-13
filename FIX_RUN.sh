#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== MIKROBOT FIX / RUN ==="

stamp="$(date +%Y%m%d_%H%M%S)"
backup=".mikrobot_backup_$stamp"
mkdir -p "$backup" static

for f in app.py index.html start.sh requirements.txt; do
  [ -f "$f" ] && cp -f "$f" "$backup/" || true
done

cat > app.py <<'PYAPP'
from __future__ import annotations
import asyncio
import os
import platform
import socket
from contextlib import asynccontextmanager
from pathlib import Path
import psutil
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

ROOT = Path(__file__).resolve().parent
PORT = int(os.getenv("PORT", "8765"))
STATIC = ROOT / "static"
INDEX = STATIC / "index.html"

@asynccontextmanager
async def lifespan(app: FastAPI):
    async def monitor():
        while True:
            await asyncio.sleep(10)
    task = asyncio.create_task(monitor())
    try:
        yield
    finally:
        task.cancel()

app = FastAPI(title="MikroBot JARVIS PRO", version="3.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False,
                   allow_methods=["*"], allow_headers=["*"])

def system_info():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu": round(psutil.cpu_percent(interval=0.05), 1),
        "ram": round(mem.percent, 1),
        "disk": round(disk.percent, 1),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
    }

def network_info():
    interfaces = []
    for name, st in psutil.net_if_stats().items():
        ips = [a.address for a in psutil.net_if_addrs().get(name, [])
               if getattr(a, "family", None) == socket.AF_INET]
        interfaces.append({"name": name, "up": bool(st.isup),
                           "speed_mbps": st.speed, "ipv4": ips})
    io = psutil.net_io_counters()
    return {"interfaces": interfaces, "bytes_sent": io.bytes_sent,
            "bytes_received": io.bytes_recv}

@app.get("/")
async def root():
    if INDEX.exists():
        return FileResponse(INDEX)
    return JSONResponse({"ok": False, "error": "static/index.html não encontrado"}, status_code=500)

@app.get("/api/health")
async def health():
    return {"ok": True, "service": "MikroBot JARVIS PRO", "version": "3.0.0", "port": PORT}

@app.get("/api/system")
async def system():
    return system_info()

@app.get("/api/network")
async def network():
    return network_info()

@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json({"type": "telemetry", **system_info()})
            await asyncio.sleep(2)
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, workers=1)

PYAPP

cat > requirements.txt <<'REQ'
fastapi>=0.116,<1
uvicorn[standard]>=0.35,<1
psutil>=7,<8

REQ

cat > static/index.html <<'HTML'
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#02070b">
<title>MikroBot JARVIS PRO</title>
<style>
:root{--bg:#02070b;--panel:#07131b;--line:#183746;--txt:#ebffff;--mut:#8aa6b0;--cyan:#00e5ff;--green:#00f5a0}
*{box-sizing:border-box}
body{margin:0;color:var(--txt);font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:radial-gradient(circle at 50% -15%,#153b45 0,transparent 45%),linear-gradient(180deg,#02070b,#07131b);min-height:100vh}
header{position:sticky;top:0;z-index:2;padding:14px 16px;background:#02070ded;border-bottom:1px solid var(--line);backdrop-filter:blur(12px)}
.top{max-width:1100px;margin:auto;display:flex;justify-content:space-between;align-items:center}
.logo{font-size:clamp(20px,5vw,34px);font-weight:950}.logo b{color:var(--cyan)}.online{color:var(--green);font-size:12px}
main{max-width:1100px;margin:auto;padding:14px}
.hero,.card{background:linear-gradient(145deg,#09161e,#061017);border:1px solid var(--line);border-radius:18px;box-shadow:0 16px 50px #0008}
.hero{padding:20px}.hero h1{margin:0;font-size:clamp(30px,8vw,54px)}.muted{color:var(--mut)}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:11px;margin-top:12px}
.card{padding:15px}.label{font-size:11px;color:var(--mut);letter-spacing:1px}.metric{font-size:28px;font-weight:900;margin-top:5px}
.bar{height:8px;background:#10262f;border-radius:99px;overflow:hidden;margin-top:7px}.fill{height:100%;width:0;background:linear-gradient(90deg,var(--cyan),var(--green));transition:width .25s}
pre{white-space:pre-wrap;word-break:break-word;background:#020609;border:1px solid #102631;border-radius:12px;padding:12px}
.actions{display:flex;flex-wrap:wrap;gap:9px;margin-top:14px}
button{border:1px solid #214451;border-radius:12px;padding:12px 14px;background:#0f2530;color:var(--txt);font-weight:800}
button.primary{border:0;background:linear-gradient(135deg,var(--cyan),var(--green));color:#001219}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:520px){.grid{grid-template-columns:1fr 1fr}.actions button{flex:1 1 44%}.metric{font-size:23px}}
</style>
</head>
<body>
<header><div class="top"><div class="logo">⚡ <b>MIKROBOT</b> JARVIS PRO</div><div class="online">● CORE ONLINE</div></div></header>
<main>
<section class="hero">
<h1>COMMAND CENTER</h1>
<p class="muted">Núcleo Python estável • telemetria • rede • interface responsiva</p>
<div class="actions">
<button class="primary" onclick="refreshAll()">⚡ ATUALIZAR</button>
<button onclick="ping()">🌐 INTERNET</button>
</div>
</section>
<section class="grid">
<div class="card"><div class="label">CPU</div><div id="cpu" class="metric">—</div><div class="bar"><div id="cb" class="fill"></div></div></div>
<div class="card"><div class="label">RAM</div><div id="ram" class="metric">—</div><div class="bar"><div id="rb" class="fill"></div></div></div>
<div class="card"><div class="label">DISCO</div><div id="disk" class="metric">—</div><div class="bar"><div id="db" class="fill"></div></div></div>
<div class="card"><div class="label">SERVIDOR</div><div id="status" class="metric" style="color:var(--green)">ONLINE</div></div>
</section>
<section class="card" style="margin-top:12px"><h2>📡 Rede</h2><pre id="network">Carregando…</pre></section>
<section class="card" style="margin-top:12px"><h2>🧠 Núcleo</h2><pre id="result">Sistema inicializado.</pre></section>
</main>
<script>
const $=id=>document.getElementById(id);
async function api(u){const r=await fetch(u);if(!r.ok)throw Error("HTTP "+r.status);return r.json()}
function meter(id,bar,v){$(id).textContent=v+"%";$(bar).style.width=Math.max(0,Math.min(100,v))+"%"}
async function refreshAll(){try{const s=await api('/api/system');meter('cpu','cb',s.cpu);meter('ram','rb',s.ram);meter('disk','db',s.disk);const n=await api('/api/network');$('network').textContent=JSON.stringify(n,null,2);$('result').textContent=JSON.stringify(s,null,2)}catch(e){$('status').textContent='ERRO';$('result').textContent=e.message}}
async function ping(){const t=performance.now();try{await fetch('https://www.gstatic.com/generate_204',{cache:'no-store'});$('result').textContent='Internet OK • '+Math.round(performance.now()-t)+' ms'}catch(e){$('result').textContent='Internet indisponível: '+e.message}}
const ws=new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws');ws.onmessage=e=>{const d=JSON.parse(e.data);meter('cpu','cb',d.cpu);meter('ram','rb',d.ram);meter('disk','db',d.disk)};refreshAll();setInterval(refreshAll,10000);
</script>
</body>
</html>

HTML

touch static/favicon.ico

python3 -m pip install -q -r requirements.txt
python3 -m py_compile app.py
python3 -c "import app; print('IMPORT OK')"

pkill -f 'uvicorn.*8765' 2>/dev/null || true
fuser -k 8765/tcp 2>/dev/null || true
sleep 2

nohup env PORT=8765 python3 -m uvicorn app:app --host 0.0.0.0 --port 8765 --workers 1 > mikrobot.log 2>&1 &
PID=$!
sleep 4

if ! kill -0 "$PID" 2>/dev/null; then
  echo "=== ERRO DO SERVIDOR ==="
  tail -80 mikrobot.log
  exit 1
fi

echo "=== HEALTH ==="
curl -fsS http://127.0.0.1:8765/api/health
echo
echo "=== HOME ==="
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:8765/
echo "=== MIKROBOT ONLINE ==="
echo "Porta: 8765"
