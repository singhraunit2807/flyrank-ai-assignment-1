from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .database import get_connection, init_db
from .reporting import REPORTS_DIR, get_report_data, render_pdf

app = FastAPI(title="PDF Report Generator", version="1.0.0")


class ReportRequest(BaseModel):
    force: bool = False


@app.on_event("startup")
def startup() -> None:
    init_db()
    REPORTS_DIR.mkdir(exist_ok=True)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/reports")
async def create_report(payload: ReportRequest | None = None) -> dict:
    payload = payload or ReportRequest()
    today = datetime.now().date().isoformat()
    with get_connection() as conn:
        if not payload.force:
            existing = conn.execute(
                "SELECT id, path FROM reports WHERE substr(created_at, 1, 10) = ? ORDER BY id DESC LIMIT 1",
                (today,),
            ).fetchone()
            if existing:
                return JSONResponse(status_code=200, content={"id": existing["id"], "file": f"/reports/{existing['id']}/file", "status": "existing"})
        report_id = conn.execute(
            "INSERT INTO reports(path, created_at) VALUES (?, ?)", ("", datetime.now().isoformat(timespec="seconds"))
        ).lastrowid
        path = REPORTS_DIR / f"{report_id}.pdf"
        data = get_report_data()
        await render_pdf(path, data)
        conn.execute("UPDATE reports SET path = ? WHERE id = ?", (str(path), report_id))
        conn.commit()
    return JSONResponse(status_code=201, content={"id": report_id, "file": f"/reports/{report_id}/file", "status": "created"})


@app.get("/reports/{report_id}")
def get_report(report_id: int) -> dict:
    with get_connection() as conn:
        row = conn.execute("SELECT id, path, created_at FROM reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"id": row["id"], "path": row["path"], "created_at": row["created_at"], "file": f"/reports/{report_id}/file"}


@app.get("/reports/{report_id}/file")
def download_report(report_id: int):
    with get_connection() as conn:
        row = conn.execute("SELECT path FROM reports WHERE id = ?", (report_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    path = Path(row["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file missing")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@app.get("/reports")
def list_reports() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT id, path, created_at FROM reports ORDER BY id DESC").fetchall()
    return [{"id": r["id"], "path": r["path"], "created_at": r["created_at"], "file": f"/reports/{r['id']}/file"} for r in rows]
