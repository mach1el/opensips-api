from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
  r = client.get("/api/v1/healthz")
  assert r.status_code == 200
  assert r.json()["status"] == "ok"
