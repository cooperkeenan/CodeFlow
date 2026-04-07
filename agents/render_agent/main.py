from fastapi import FastAPI

app = FastAPI(title="Render Agent")


@app.get("/health")
async def health():
    return {"status": "ok"}