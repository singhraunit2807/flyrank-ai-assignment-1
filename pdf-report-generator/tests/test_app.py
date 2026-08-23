from fastapi.testclient import TestClient

from app.main import app
from app.database import DB_PATH, get_connection, init_db
from scripts.seed import main as seed_main


def setup_module():
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
    seed_main()


def test_health():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_seed_count():
    with get_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 200


def test_unknown_report():
    with TestClient(app) as client:
        assert client.get("/reports/999999").status_code == 404


def test_report_generation_and_idempotency():
    with TestClient(app) as client:
        first = client.post("/reports")
        assert first.status_code == 201
        first_data = first.json()
        second = client.post("/reports")
        assert second.status_code == 200
        assert second.json()["id"] == first_data["id"]
        force = client.post("/reports", json={"force": True})
        assert force.status_code == 201
        assert force.json()["id"] != first_data["id"]
        file_response = client.get(first_data["file"])
        assert file_response.status_code == 200
        assert file_response.headers["content-type"] == "application/pdf"
