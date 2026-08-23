from fastapi.testclient import TestClient

from main import app, reports

client = TestClient(app)


def setup_function():
    reports.clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_topic_is_400():
    response = client.post("/reports", json={})
    assert response.status_code == 400


def test_report_is_created_pending():
    response = client.post("/reports", json={"topic": "cats"})
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert body["id"] in reports


def test_unknown_report_is_404():
    response = client.get("/reports/does-not-exist")
    assert response.status_code == 404
