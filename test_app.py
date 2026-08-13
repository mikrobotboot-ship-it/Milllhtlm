from fastapi.testclient import TestClient
from app import app
c=TestClient(app)
def test_health():
    r=c.get("/api/health"); assert r.status_code==200 and r.json()["ok"]
def test_home():
    r=c.get("/"); assert r.status_code==200 and "MIKROBOT" in r.text
def test_offline():
    r=c.post("/api/offline",json={"text":"analise este mikrotik"}); assert r.status_code==200
def test_validate():
    r=c.post("/api/validate-script",json={"text":"/ip address print"}); assert r.status_code==200
