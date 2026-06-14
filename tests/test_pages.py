from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    with TestClient(create_app(tmp_path / "queue.sqlite3")) as test_client:
        yield test_client


def test_take_number_page_has_two_priority_buttons(client: TestClient):
    resp = client.get("/take-number")
    assert resp.status_code == 200
    assert 'id="take-vip-btn"' in resp.text
    assert 'id="take-normal-btn"' in resp.text


def test_call_station_page_has_call_and_repeat_buttons(client: TestClient):
    resp = client.get("/station/station-1")
    assert resp.status_code == 200
    assert 'id="call-next-btn"' in resp.text
    assert 'id="repeat-call-btn"' in resp.text
