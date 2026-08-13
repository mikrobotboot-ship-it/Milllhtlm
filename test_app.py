from fastapi.testclient import TestClient
from app import app
c=TestClient(app)
def test_health():
    r=c.get('/api/health'); assert r.status_code==200 and r.json()['ok']
def test_index():
    r=c.get('/'); assert r.status_code==200 and 'MIKROBOT' in r.text
def test_validate():
    r=c.post('/api/validate-script',json={'script':'/ip address print','routeros_version':'7'}); assert r.status_code==200
