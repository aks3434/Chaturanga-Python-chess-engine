import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from .routers import games, ws  # noqa: E402
from .game import registry  # noqa: E402


async def _idle_reaper():
    """Background task: kills engine subprocesses for games nobody's touched in a while."""
    while True:
        await asyncio.sleep(60)
        for session in registry.all_sessions():
            if session.is_idle():
                try:
                    await session.engine_session.stop()
                finally:
                    registry.remove(session.game_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    reaper_task = asyncio.create_task(_idle_reaper())
    yield
    reaper_task.cancel()
    # Clean up any still-running engine processes on shutdown
    for session in registry.all_sessions():
        await session.engine_session.stop()


app = FastAPI(title="Chess Engine API", lifespan=lifespan)

default_origins = ",".join(
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
)
allowed_origins = os.environ.get("ALLOWED_ORIGINS", default_origins).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(games.router)
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok", "active_games": registry.count()}
