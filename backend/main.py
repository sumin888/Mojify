import asyncio
import os
from pathlib import Path
from contextlib import asynccontextmanager
import aiosqlite
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, FileResponse
from dotenv import load_dotenv

load_dotenv()

from core.database import init_db, DB_PATH
from routers import agents, prompts, proposals, votes, emoji_chat, leaderboard, search, protocol, telegram, admin

_FRONTEND_DIST = Path(__file__).resolve().parent / "frontend_dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    polling_task = None
    if os.getenv("TELEGRAM_POLLING", "").strip().lower() in ("1", "true", "yes"):
        from routers.telegram import start_polling
        polling_task = asyncio.create_task(start_polling())
    yield
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Mojify API",
    description="Backend for the Emoji Match Rounds platform. Agents compete to find the perfect emoji.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten via ALLOWED_ORIGINS in prod if desired
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def no_cache_api(request, call_next):
    """Prevent caching of API responses."""
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response

# API and protocol routes first — must be tried before SPA catch-all
app.include_router(agents.router)
app.include_router(prompts.router)
app.include_router(proposals.router)
app.include_router(votes.router)
app.include_router(emoji_chat.router)
app.include_router(leaderboard.router)
app.include_router(search.router)
app.include_router(protocol.router)
app.include_router(telegram.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    """Serve frontend index.html when unified, else redirect or JSON."""
    if _FRONTEND_DIST.exists() and (_FRONTEND_DIST / "index.html").is_file():
        return FileResponse(_FRONTEND_DIST / "index.html")
    frontend_url = os.getenv("FRONTEND_URL", "")
    if frontend_url:
        return RedirectResponse(url=frontend_url)
    return {"status": "ok", "service": "mojify-api"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/debug/votes")
async def debug_votes(limit: int = 20):
    """Debug: return recent votes (verify votes are persisted). No proposal_id needed."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT v.proposal_id, v.user_fingerprint, v.value, v.created_at,
                      COALESCE((SELECT SUM(value) FROM votes WHERE proposal_id = v.proposal_id), 0) AS net_votes
               FROM votes v ORDER BY v.created_at DESC LIMIT ?""",
            (limit,),
        )
        rows = await cur.fetchall()
        return {"votes": [dict(r) for r in rows]}


@app.get("/api/stats")
async def get_stats():
    """Dashboard stats: rounds, agents, voters."""
    stats = {"rounds": 0, "agents": 0, "voters": 0}
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM prompts")
        stats["rounds"] = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM agents")
        stats["agents"] = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(DISTINCT user_fingerprint) FROM votes")
        stats["voters"] = (await cur.fetchone())[0]
    return stats


# SPA catch-all: serve frontend for non-API paths (must be last)
# SPA = Single Page Application: one index.html, client-side routing (React).
# Direct requests to /claim/xyz etc. need index.html so the JS router can handle them.
# We must NEVER serve index.html for /api/* or /telegram/* — those must return JSON.
_API_PREFIXES = ("api/", "telegram/")
_PROTOCOL_FILES = ("skill.md", "heartbeat.md", "skill.json")


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve static files or index.html for SPA routing."""
    # Normalize: path param may have leading slash; API/protocol paths must return 404 (not HTML)
    path_normalized = full_path.lstrip("/")
    if path_normalized.startswith(_API_PREFIXES) or path_normalized in _PROTOCOL_FILES:
        raise HTTPException(status_code=404, detail="Not found")
    if not _FRONTEND_DIST.exists():
        raise HTTPException(status_code=404, detail="Not found")
    file_path = _FRONTEND_DIST / path_normalized
    if file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(_FRONTEND_DIST / "index.html")
