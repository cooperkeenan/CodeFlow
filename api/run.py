import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config("main:app", host="127.0.0.1", port=8000)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())
