from fastapi import FastAPI

app = FastAPI(title="Profiler Agent")


@app.get("/health")
async def health():
    return {"status": "ok"}