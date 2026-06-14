from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    with TestClient(create_app(tmp_path / "queue.sqlite3")) as test_client:
        yield test_client


def test_take_ticket_and_call_next(client: TestClient):
    resp = client.post("/api/tickets", json={"priority": "vip"})
    assert resp.status_code == 200
    assert resp.json()["ticket_no"] == "VIP-001"

    resp = client.post("/api/stations/station-1/next")
    assert resp.status_code == 200
    assert resp.json()["station_id"] == "station-1"


def test_repeat_call_returns_same_announcement(client: TestClient):
    client.post("/api/tickets", json={"priority": "normal"})
    first = client.post("/api/stations/station-1/next").json()

    repeat = client.post("/api/stations/station-1/repeat")

    assert repeat.status_code == 200
    assert repeat.json()["ticket_no"] == first["ticket_no"]
    assert repeat.json()["announcement_text"] == first["announcement_text"]


def test_websocket_receives_queue_updates(client: TestClient):
    with client.websocket_connect("/ws") as ws:
        client.post("/api/tickets", json={"priority": "normal"})
        msg = ws.receive_json()
        assert msg["type"] == "queue_snapshot"
