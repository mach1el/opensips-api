from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_and_list_items():
  r = client.post("/api/v1/items", json={"name": "foo", "description": "bar"})
  assert r.status_code == 201
  created = r.json()
  assert created["name"] == "foo"

  r2 = client.get("/api/v1/items")
  assert r2.status_code == 200
  data = r2.json()
  assert data["total"] >= 1
