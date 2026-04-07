from fastapi import FastAPI

app = FastAPI(title="Platform Orchestrator")


@app.get("/health")
async def health():
    return {"status": "ok"}