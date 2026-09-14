from __future__ import annotations

import pytest
from src.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_dashboard(client):
    res = client.get("/")
    assert res.status_code == 200
    assert b"TaskPulse" in res.data
    assert b"Intake Studio" in res.data


def test_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["ok"] is True
    assert json_data["status"] == "online"


def test_readiness_check(client):
    res = client.get("/api/readiness")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["ok"] is True
    assert json_data["mode"] == "sqlite"


def test_intake_api(client):
    res = client.post("/api/intake", json={
        "text": "Complete client integration for 45 mins urgent, then write tests for 30 mins"
    })
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data["ok"] is True
    assert "plan" in json_data
    assert "telemetry" in json_data


def test_ideas_api(client):
    # Create idea
    create_res = client.post("/api/ideas", json={"content": "Test brilliant idea"})
    assert create_res.status_code == 201

    # List ideas
    list_res = client.get("/api/ideas")
    assert list_res.status_code == 200
    ideas = list_res.get_json()["ideas"]
    assert any(i["content"] == "Test brilliant idea" for i in ideas)


def test_telemetry_api(client):
    res = client.get("/api/telemetry")
    assert res.status_code == 200
    data = res.get_json()
    assert "telemetry" in data
    assert "avg_latency_ms" in data["telemetry"]
