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
