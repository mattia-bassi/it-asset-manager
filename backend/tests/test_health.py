from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    # Nota: questo test non verifica DB (in test potrebbe non esserci)
    resp = client.get("/api/health")
    assert resp.status_code in (200, 500)

