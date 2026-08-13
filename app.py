import asyncio
import json
import os
import platform
import re
import socket
from contextlib import asynccontextmanager
from pathlib import Path

import psutil
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
PORT = int(os.getenv("PORT", "8765"))
KNOWLEDGE_FILE = ROOT / "knowledge.json"

@asynccontextmanager
async def lifespan(app: FastAPI):
    async def watchdog():
        while True:
            await asyncio.sleep(10)
    task = asyncio.create_task(watchdog())
    try:
        yield
    finally:
        task.cancel()

app = FastAPI(title="MikroBot JARVIS PRO OFFLINE", version="4.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextBody(BaseModel):
    text: str

def system_info():
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu": round(psutil.cpu_percent(0.05), 1),
        "ram": round(vm.percent, 1),
        "disk": round(disk.percent, 1),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "mode": "offline-first",
    }

def network_info():
    items = []
    for name, st in psutil.net_if_stats().items():
        ipv4 = [
            a.address for a in psutil.net_if_addrs().get(name, [])
            if getattr(a, "family", None) == socket.AF_INET
        ]
        items.append({
            "name": name,
            "up": bool(st.isup),
            "speed_mbps": st.speed,
            "ipv4": ipv4,
        })
    io = psutil.net_io_counters()
    return {
        "interfaces": items,
        "bytes_sent": io.bytes_sent,
        "bytes_received": io.bytes_recv,
    }

def knowledge():
    try:
        return json.loads(KNOWLEDGE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def offline_answer(text: str):
    q = text.lower().strip()
    if not q:
        return {"mode": "offline", "answer": "Digite um comando ou pergunta."}

    if any(k in q for k in ("mikrotik", "routeros", "wan", "lan", "bridge")):
        return {
            "mode": "offline",
            "answer": (
                "Modo offline: posso analisar estrutura básica de RouterOS, "
                "identificar WAN/LAN/bridge/DHCP/PPPoE/NAT/VLAN e sugerir uma sequência segura. "
                "Não executo alterações automaticamente."
            ),
            "next": "Cole o script em 🛠️ MikroTik → Validar.",
        }

    if any(k in q for k in ("internet", "rede", "wifi", "wi-fi", "5g", "latência")):
        return {
            "mode": "offline",
            "answer": (
                "Modo offline: o núcleo consegue verificar interfaces, IPs, CPU/RAM e estado da rede local. "
                "Teste externo depende de Internet disponível."
            ),
            "next": "Abra 📡 Rede para ver interfaces locais.",
        }

    if any(k in q for k in ("camera", "câmera", "hikvision", "milesight", "onvif", "rtsp")):
        return {
            "mode": "offline",
            "answer": (
                "Assistente offline de câmeras ativo. Posso orientar por ONVIF/RTSP, IP, "
                "PoE, NTP e credenciais autorizadas. A configuração exata depende do modelo/firmware."
            ),
            "next": "Abra 📷 Câmeras e escolha o fabricante.",
        }

    if any(k in q for k in ("whatsapp", "mensagem")):
        return {
            "mode": "offline",
            "answer": "O módulo local está disponível, mas envio real de WhatsApp exige a API oficial e Internet.",
        }

    return {
        "mode": "offline",
        "answer": (
            "JARVIS OFFLINE ativo. Posso responder a consultas do dicionário local, "
            "diagnosticar recursos do sistema, analisar scripts básicos e orientar rede/câmeras."
        ),
        "next": "Experimente: 'analise este script MikroTik'.",
    }

def validate_script(script: str):
    s = script.strip()
    errors = []
    warnings = []
    if not s:
        errors.append("Script vazio.")
    if s.count("{") != s.count("}"):
        errors.append("Chaves desbalanceadas.")
    if s.count('"') % 2:
        errors.append("Aspas duplas desbalanceadas.")

    dangerous = (
        "/system reset-configuration",
        "/file remove",
        "/user remove",
        "/system reboot",
        "/system shutdown",
    )
    for term in dangerous:
        if term in s.lower():
            warnings.append("Ação sensível detectada: " + term)

    if "ether1" in s.lower() and "bridge" in s.lower() and "wan" in s.lower():
        warnings.append("Confirme que a WAN não foi colocada na bridge-LAN.")

    if "pppoe" in s.lower() and "dhcp-client" in s.lower():
        warnings.append("Confira se PPPoE e DHCP-client não estão disputando a mesma WAN.")

    if "dhcp-server" in s.lower() and "192.168." not in s:
        warnings.append("DHCP detectado; confirme a rede/pool antes de aplicar.")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "mode": "offline",
        "message": "Nenhuma alteração foi executada."
    }

@app.get("/")
async def root():
    path = STATIC / "index.html"
    if not path.exists():
        return JSONResponse({"ok": False, "error": "static/index.html não encontrado"}, status_code=500)
    return FileResponse(path)

@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse(STATIC / "manifest.webmanifest", media_type="application/manifest+json")

@app.get("/sw.js")
async def sw():
    return FileResponse(STATIC / "sw.js", media_type="application/javascript")

@app.get("/api/health")
async def health():
    return {"ok": True, "service": "MikroBot JARVIS PRO OFFLINE", "version": "4.0.0", "port": PORT}

@app.get("/api/system")
async def system():
    return system_info()

@app.get("/api/network")
async def network():
    return network_info()

@app.get("/api/knowledge")
async def knowledge_route():
    return knowledge()

@app.post("/api/offline")
async def offline(body: TextBody):
    return offline_answer(body.text)

@app.post("/api/validate-script")
async def validate(body: TextBody):
    return validate_script(body.text)

@app.post("/api/camera")
async def camera(body: TextBody):
    brand = body.text.lower().strip()
    profiles = {
        "hikvision": {
            "brand": "Hikvision",
            "protocols": ["ONVIF", "RTSP", "HTTP/HTTPS"],
            "checks": ["modelo", "firmware", "IP", "NTP", "PoE", "usuário autorizado"],
        },
        "milesight": {
            "brand": "Milesight",
            "protocols": ["ONVIF", "RTSP", "HTTP/HTTPS"],
            "checks": ["modelo", "firmware", "IP", "NTP", "PoE", "usuário autorizado"],
        },
        "generic": {
            "brand": "ONVIF/RTSP",
            "protocols": ["ONVIF", "RTSP"],
            "checks": ["descoberta", "IP", "NTP", "stream", "usuário autorizado"],
        }
    }
    return profiles.get(brand, profiles["generic"])

@app.get("/api/internet-status")
async def internet_status():
    return {"browser_mode": True, "message": "O estado da Internet do aparelho é detectado pelo navegador."}

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({"type": "telemetry", **system_info()})
            await asyncio.sleep(2)
    except Exception:
        pass
