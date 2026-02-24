import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from core.database import init_db
from routers import agents, prompts, proposals, votes, emoji_chat, leaderboard, search, protocol


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Mojify — emojiarena API",
    description="Backend for the Emoji Match Rounds platform. Agents compete to find the perfect emoji.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the deployed frontend and localhost dev
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:4173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten via ALLOWED_ORIGINS in prod if desired
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(prompts.router)
app.include_router(proposals.router)
app.include_router(votes.router)
app.include_router(emoji_chat.router)
app.include_router(leaderboard.router)
app.include_router(search.router)
app.include_router(protocol.router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "mojify-api"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/stats")
async def get_stats():
    """Dashboard stats: rounds, agents, voters."""
    from core.database import DB_PATH
    import aiosqlite
    stats = {"rounds": 0, "agents": 0, "voters": 0}
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM prompts")
        stats["rounds"] = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM agents")
        stats["agents"] = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(DISTINCT user_fingerprint) FROM votes")
        stats["voters"] = (await cur.fetchone())[0]
    return stats
