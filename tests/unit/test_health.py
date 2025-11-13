import asyncio
from fastapi.testclient import TestClient

from quant_web.main import app


client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_download_endpoint():
    payload = {
        "stock_list": ["000001.SZ"],
        "start_date": "20230101",
        "end_date": "20231231",
        "source": "akshare"
    }
    r = client.post("/api/v1/data/download", json=payload)
    assert r.status_code == 202
    body = r.json()
    assert "task_id" in body
