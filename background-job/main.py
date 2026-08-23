from fastapi import FastAPI

app = FastAPI(title="Your First Background Job")

@app.get("/health")
async def health():
    return {"status": "ok"}
