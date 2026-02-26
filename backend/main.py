import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from database import init_db
from routers import agents, prompts, proposals, votes, emoji_chat, leaderboard


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
    "http://localhost:5173,http://localhost:3000,http://localhost:4173,https://mojify-production-7b9d.up.railway.app",
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


@app.get("/")
async def root():
    return {"status": "ok", "service": "mojify-api"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
