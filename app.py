
from __future__ import annotations

import asyncio
import json
import os
import platform
import socket
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import psutil
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DB = ROOT / "mikrobot.db"

PORT = int(os.getenv("PORT", "8765"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
OPENAI_BASE = os.getenv("OPENAI_BASE", "https://api.openai.com/v1")

WA_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WA_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "")
WA_VERIFY = os.getenv("WHATSAPP_VERIFY_TOKEN", "")

app = FastAPI(title="MikroBot JARVIS PRO", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextRequest(BaseModel):
    text: str

class RscRequest(BaseModel):
    script: str
    routeros_version: str = "unknown"

class SpeedResult(BaseModel):
    target: str = "browser"

def now():
    return datetime.now(timezone.utc).isoformat()

def db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        kind TEXT NOT NULL,
        data TEXT NOT NULL
    )""")
    c.commit()
    return c

def log_event(kind: str, data: Any):
    with db() as c:
        c.execute(
            "INSERT INTO events(ts,kind,data) VALUES(?,?,?)",
            (now(), kind, json.dumps(data, ensure_ascii=False)[:8000])
        )

def system_snapshot():
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu": round(psutil.cpu_percent(interval=0.05), 1),
        "ram": round(vm.percent, 1),
        "ram_used_mb": round(vm.used / 1048576),
        "ram_total_mb": round(vm.total / 1048576),
        "disk": round(disk.percent, 1),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "hostname": socket.gethostname(),
        "workers": 1,
    }

def network_snapshot():
    interfaces = []
    for name, st in psutil.net_if_stats().items():
        ips = [
            a.address for a in psutil.net_if_addrs().get(name, [])
            if getattr(a, "family", None) == socket.AF_INET
        ]
        interfaces.append({
            "name": name,
            "up": bool(st.isup),
            "speed_mbps": st.speed,
            "ipv4": ips,
        })
    io = psutil.net_io_counters()
    return {
        "interfaces": interfaces,
        "bytes_sent": io.bytes_sent,
        "bytes_received": io.bytes_recv,
    }

def local_rsc_checks(script: str, version: str):
    s = script.strip()
    lower = s.lower()
    warnings: list[str] = []
    errors: list[str] = []

    if not s:
        errors.append("Script vazio.")

    if s.count("{") != s.count("}"):
        errors.append("Chaves { } desbalanceadas.")

    if s.count('"') % 2:
        errors.append("Aspas duplas desbalanceadas.")

    destructive = [
        "/system reset-configuration",
        "/file remove",
        "/user remove",
        "/system shutdown",
        "/system reboot",
    ]
    for term in destructive:
        if term in lower:
            warnings.append(f"Ação potencialmente destrutiva detectada: {term}")

    if "password=" in lower or "private-key" in lower:
        warnings.append("Possível segredo embutido no script. Remova antes de compartilhar.")

    if "add-default-route" in lower and "pppoe" in lower:
        warnings.append("Confira se há somente uma rota default válida.")

    if "bridge" in lower and "ether1" in lower and "wan" in lower:
        warnings.append("Confirme que a WAN não foi colocada na bridge-LAN.")

    if version != "unknown":
        warnings.append(f"Compatibilidade solicitada para RouterOS: {version}.")
    else:
        warnings.append("RouterOS não informado; compatibilidade específica não pode ser garantida.")

    return {
        "syntax_basic_ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "requires_manual_validation": True,
    }

async def openai_responses(input_text: str, web: bool = False):
    if not OPENAI_API_KEY:
        return {
            "ok": False,
            "provider": "unconfigured",
            "error": "OPENAI_API_KEY não configurada."
        }

    payload: dict[str, Any] = {
        "model": OPENAI_MODEL,
        "input": input_text,
    }
    if web:
        payload["tools"] = [{"type": "web_search"}]

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            r = await client.post(
                f"{OPENAI_BASE}/responses",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        r.raise_for_status()
        data = r.json()
        return {
            "ok": True,
            "provider": "openai",
            "model": OPENAI_MODEL,
            "text": data.get("output_text", ""),
            "raw": data,
        }
    except Exception as exc:
        return {
            "ok": False,
            "provider": "openai",
            "error": str(exc)[:500],
        }

async def internet_probe():
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=6, follow_redirects=True) as client:
            r = await client.get("https://www.gstatic.com/generate_204")
        return {
            "online": r.status_code in (200, 204),
            "http_status": r.status_code,
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    except Exception as exc:
        return {"online": False, "error": str(exc)[:220]}

async def whatsapp_send(to: str, text: str):
    if not (WA_TOKEN and WA_PHONE_ID and WA_API_VERSION):
        return {"ok": False, "error": "WhatsApp Cloud API não configurada."}

    url = f"https://graph.facebook.com/{WA_API_VERSION}/{WA_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4096]},
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                url,
                headers={"Authorization": f"Bearer {WA_TOKEN}"},
                json=payload,
            )
        return {"ok": r.is_success, "status": r.status_code, "body": r.text[:1000]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:300]}

@app.get("/")
async def root():
    return FileResponse(STATIC / "index.html")

@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "service": "MikroBot JARVIS PRO",
        "version": "2.0.0",
        "port": PORT,
    }

@app.get("/api/system")
async def system():
    return system_snapshot()

@app.get("/api/network")
async def network():
    return network_snapshot()

@app.get("/api/internet")
async def internet():
    result = await internet_probe()
    log_event("internet", result)
    return result

@app.get("/api/events")
async def events():
    with db() as c:
        rows = c.execute(
            "SELECT ts,kind,data FROM events ORDER BY id DESC LIMIT 50"
        ).fetchall()
    return [{"ts": a, "kind": b, "data": c} for a, b, c in rows]

@app.post("/api/ai")
async def ai(req: TextRequest):
    result = await openai_responses(
        "Você é o núcleo JARVIS técnico. Responda em português, "
        "explique raciocínio de forma resumida, proponha verificações "
        "antes de mudanças e nunca invente credenciais.\n\n"
        + req.text
    )
    log_event("ai", req.text)
    return result

@app.post("/api/research")
async def research(req: TextRequest):
    prompt = (
        "Pesquise na web por fontes atuais e confiáveis sobre o tema abaixo. "
        "Priorize documentação oficial, fabricantes e fontes técnicas confiáveis. "
        "Resuma os achados, destaque data/versão quando relevante e inclua as fontes.\n\n"
        + req.text
    )
    result = await openai_responses(prompt, web=True)
    log_event("research", req.text)
    return result

@app.post("/api/validate-script")
async def validate_script(req: RscRequest):
    result = local_rsc_checks(req.script, req.routeros_version)
    log_event("rsc_validate", result)
    return result

@app.post("/api/repair-script")
async def repair_script(req: RscRequest):
    checks = local_rsc_checks(req.script, req.routeros_version)
    prompt = (
        "Você é um especialista em MikroTik RouterOS e engenharia de redes. "
        "Revise o script abaixo para a versão informada. "
        "Identifique incompatibilidades, lógica incorreta e riscos. "
        "Depois gere uma versão corrigida em bloco RSC, sem inventar "
        "interfaces, endereços, usuários, senhas ou valores não informados. "
        "Inclua um bloco de validação/checagem e explique o que mudou. "
        "Não execute o script.\n\n"
        f"ROUTEROS: {req.routeros_version}\n"
        f"CHECKS LOCAIS: {json.dumps(checks, ensure_ascii=False)}\n"
        f"SCRIPT:\n{req.script}"
    )
    result = await openai_responses(prompt, web=True)
    result["local_checks"] = checks
    log_event("rsc_repair", result)
    return result

@app.post("/api/speedtest")
async def speedtest():
    # O backend mede a conexão do Codespace. Para medir o 5G/Wi-Fi do aparelho,
    # o frontend executa o teste leve diretamente no navegador.
    t = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get("https://speed.cloudflare.com/__down?bytes=1048576")
        seconds = max(time.perf_counter() - t, 0.001)
        mbps = round((len(r.content) * 8 / seconds) / 1_000_000, 1)
        return {"ok": True, "mbps": mbps, "bytes": len(r.content)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:250]}

@app.post("/api/camera/profile")
async def camera_profile(req: TextRequest):
    brand = req.text.lower().strip()
    profiles = {
        "hikvision": {
            "protocols": ["ONVIF", "RTSP", "HTTP/HTTPS"],
            "checks": ["modelo/firmware", "IP", "usuário autorizado", "porta RTSP/HTTP", "hora/NTP"],
        },
        "milesight": {
            "protocols": ["ONVIF", "RTSP", "HTTP/HTTPS"],
            "checks": ["modelo/firmware", "IP", "credenciais autorizadas", "perfil ONVIF", "RTSP"],
        },
        "generic": {
            "protocols": ["ONVIF", "RTSP"],
            "checks": ["descoberta do modelo", "IP", "firmware", "ONVIF", "RTSP"],
        },
    }
    return profiles.get(brand, profiles["generic"])

@app.post("/api/whatsapp/send")
async def whatsapp_route(req: Request):
    body = await req.json()
    return await whatsapp_send(str(body.get("to", "")), str(body.get("text", "")))

@app.get("/webhook/whatsapp")
async def whatsapp_verify(request: Request):
    q = request.query_params
    if WA_VERIFY and q.get("hub.verify_token") == WA_VERIFY:
        return int(q.get("hub.challenge", "0"))
    return JSONResponse({"ok": False}, status_code=403)

@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    log_event("whatsapp_webhook", data)
    return {"ok": True}

@app.get("/api/knowledge")
async def knowledge():
    p = ROOT / "knowledge.json"
    return json.loads(p.read_text(encoding="utf-8"))

@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()
    while True:
        try:
            s = system_snapshot()
            await ws.send_json({"type": "telemetry", **s})
            await asyncio.sleep(2)
        except Exception:
            break

@app.on_event("startup")
async def startup():
    init_db()
    async def optimizer():
        while True:
            # Ciclo de 10 s: monitora apenas o próprio app e evita trabalho
            # agressivo quando RAM/CPU estiverem sob pressão.
            snap = system_snapshot()
            if snap["ram"] > 90 or snap["cpu"] > 90:
                log_event("optimizer", {
                    "action": "pressure_detected",
                    "cpu": snap["cpu"],
                    "ram": snap["ram"],
                    "policy": "reduce_internal_polling_only",
                })
            await asyncio.sleep(10)
    asyncio.create_task(optimizer())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
