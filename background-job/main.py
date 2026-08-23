import logging
import threading
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import inngest
from inngest.fast_api import serve

app = FastAPI(title="Your First Background Job")
logger = logging.getLogger("background-job-api")

reports: dict[str, dict[str, Any]] = {}
reports_lock = threading.Lock()

inngest_client = inngest.Inngest(app_id="report-api", is_production=False, logger=logger)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/reports", status_code=202)
async def create_report(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"detail": "Request body must be valid JSON"})
    if not isinstance(payload, dict) or not isinstance(payload.get("topic"), str) or not payload["topic"].strip():
        return JSONResponse(status_code=400, content={"detail": "topic is required"})
    topic = payload["topic"].strip()
    report_id = uuid.uuid4().hex
    with reports_lock:
        reports[report_id] = {"id": report_id, "topic": topic, "status": "pending"}
    await inngest_client.send(inngest.Event(
        name="report/requested",
        data={"id": report_id, "topic": topic},
        id=report_id,
    ))
    return JSONResponse(status_code=202, content={"id": report_id, "status": "pending"})

@app.get("/reports/{report_id}")
async def get_report(report_id: str) -> dict[str, Any]:
    with reports_lock:
        record = reports.get(report_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Report not found")
        return dict(record)

@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context) -> str:
    await ctx.step.sleep("hello-delay", "5s")
    return "Hello from the background!"

@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
    retries=2,
)
async def make_report(ctx: inngest.Context) -> dict[str, Any]:
    report_id = str(ctx.event.data["id"])
    topic = str(ctx.event.data["topic"])
    with reports_lock:
        existing = reports.get(report_id)
        if existing is None:
            return {"id": report_id, "status": "missing"}
        if existing.get("status") == "done":
            return dict(existing)
    await ctx.step.sleep("do-the-slow-work", "8s")
    def build_report() -> dict[str, Any]:
        if topic.lower() == "fail":
            raise RuntimeError("The report oven is broken!")
        result = {
            "title": f"Report about {topic}",
            "summary": f"Background report generated for topic: {topic}.",
            "source": "background-job-demo",
        }
        with reports_lock:
            reports[report_id] = {"id": report_id, "topic": topic, "status": "done", "result": result}
        return result
    result = await ctx.step.run("build-report", build_report)
    return {"id": report_id, "status": "done", "result": result}

serve(app, ingest_client, [say_hello, make_report])
