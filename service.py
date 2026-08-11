#!/usr/bin/env python3
import json, os, platform, socket, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "mikrobot.html"
DEFAULT_PORT = 8765

def choose_port():
    try:
        p = int(os.environ.get("PORT", str(DEFAULT_PORT)))
        return p if 1 <= p <= 65535 else DEFAULT_PORT
    except ValueError:
        return DEFAULT_PORT

def json_out(handler, data, status=200):
    raw = json.dumps(data, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(raw)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[HTTP]", fmt % args)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return json_out(self, {"ok":True,"service":"MikroBot Pro X","port":PORT,"python":platform.python_version()})
        if path == "/api/system":
            return json_out(self, {"ok":True,"os":platform.platform(),"python":platform.python_version(),"hostname":socket.gethostname()})
        if path == "/api/network":
            try:
                host=socket.gethostname()
                ip=socket.gethostbyname(host)
            except Exception:
                ip="indisponível"
            return json_out(self, {"ok":True,"hostname":host,"local_ip":ip})
        if path == "/api/internet":
            t=time.time()
            try:
                with urllib.request.urlopen("https://www.google.com/generate_204", timeout=4) as r:
                    return json_out(self, {"ok":True,"http_status":r.status,"latency_ms":round((time.time()-t)*1000,1)})
            except Exception as e:
                return json_out(self, {"ok":False,"error":str(e)})
        if path == "/api/diagnostic":
            return json_out(self, {"ok":True,"diagnostic":[
                "Serviço Python respondendo.",
                "Interface HTML carregada.",
                "Para MikroTik, valide WAN, gateway, DNS, DHCP/PPPoE, bridge e firewall.",
                "Não são executadas alterações automáticas no equipamento."
            ]})
        if path in ("/","/index.html"):
            try:
                raw=HTML.read_bytes()
            except FileNotFoundError:
                return json_out(self, {"ok":False,"error":"mikrobot.html não encontrado"},404)
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers(); self.wfile.write(raw); return
        self.send_error(404)

    def do_POST(self):
        path=urlparse(self.path).path
        if path != "/api/analyze": return self.send_error(404)
        try:
            n=int(self.headers.get("Content-Length","0"))
            body=json.loads(self.rfile.read(n) or b"{}")
            cfg=str(body.get("config",""))
            checks=[]
            low=cfg.lower()
            for term,label in [("interface","interfaces"),("bridge","bridge"),("dhcp","DHCP"),("pppoe","PPPoE"),("firewall","firewall"),("dns","DNS"),("ip address","endereços IP")]:
                if term in low: checks.append(f"Encontrado: {label}")
            return json_out(self, {"ok":True,"checks":checks or ["Nenhum bloco reconhecido; revise o texto inserido."],"note":"Análise somente informativa; revise antes de aplicar mudanças."})
        except Exception as e:
            return json_out(self, {"ok":False,"error":str(e)},400)

PORT=choose_port()
server=ThreadingHTTPServer(("0.0.0.0",PORT),Handler)
print(f"MikroBot Pro X — Python Core em http://0.0.0.0:{PORT}")
try: server.serve_forever()
except KeyboardInterrupt: pass
finally: server.server_close()
