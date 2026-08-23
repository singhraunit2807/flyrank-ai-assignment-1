import logging

from fastapi import FastAPI
import inngest
from inngest.fast_api import serve

app = FastAPI(title="Your First Background Job")
logger = logging.getLogger("background-job-api")

inngest_client = inngest.Inngest(app_id="report-api", is_production=False, logger=logger)

@app.get("/health")
async def health():
    return {"status": "ok"}

@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context) -> str:
    await ctx.step.sleep("hello-delay", "5s")
    return "Hello from the background!"

serve(app, inngest_client, [say_hello])
