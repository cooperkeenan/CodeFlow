from fastapi import FastAPI

app = FastAPI(title="Tracer Agent")


@app.get("/health")
async def health():
    return {"status": "ok"}