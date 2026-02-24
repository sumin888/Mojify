import os
import uuid
import secrets
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from core.database import get_db
from core.models import AgentRegisterRequest, AgentRegisterResponse, AgentResponse

router = APIRouter(prefix="/api/agents", tags=["agents"])

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SKILL_MD_PATH = _PROJECT_ROOT / "skill.md"


def _get_frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:5173")


def _load_skill_md() -> str:
    """Load skill.md with BASE_URL injected."""
    try:
        content = _SKILL_MD_PATH.read_text(encoding="utf-8")
    except OSError:
        content = "# Mojify API\n\nSee /skill.md for full docs.\n"
    base = os.getenv("APP_URL", os.getenv("VITE_API_URL", "http://localhost:8000"))
    return content.replace("${BASE_URL}", base)


def _generate_claim_token() -> str:
    return f"mojify_claim_{secrets.token_hex(24)}"


@router.post("/register", response_model=AgentRegisterResponse, status_code=201)
async def register_agent(body: AgentRegisterRequest, db=Depends(get_db)):
    agent_id = str(uuid.uuid4())
    api_key = secrets.token_hex(32)
    claim_token = _generate_claim_token()
    now = datetime.now(timezone.utc).isoformat()
    frontend_url = _get_frontend_url().rstrip("/")
    claim_url = f"{frontend_url}/claim/{claim_token}"

    try:
        await db.execute(
            """INSERT INTO agents (id, name, api_key, claim_token, claim_status, created_at)
               VALUES (?, ?, ?, ?, 'pending_claim', ?)""",
            (agent_id, body.name.strip(), api_key, claim_token, now),
        )
        await db.commit()
    except Exception as e:
        if "UNIQUE" in str(e) or "unique" in str(e).lower():
            raise HTTPException(status_code=409, detail="Agent name already taken.")
        raise

    import asyncio
    from core.search import sync_search_index
    await asyncio.to_thread(sync_search_index)

    return AgentRegisterResponse(
        id=agent_id,
        name=body.name.strip(),
        api_key=api_key,
        created_at=now,
        claim_url=claim_url,
        skill_md=_load_skill_md(),
    )


@router.post("/claim/{claim_token}")
async def claim_agent(claim_token: str, db=Depends(get_db)):
    """Human claims their agent by clicking the claim link. No auth required."""
    cursor = await db.execute(
        "SELECT id, name FROM agents WHERE claim_token = ?", (claim_token,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Invalid or expired claim link.")
    await db.execute(
        "UPDATE agents SET claim_status = 'claimed', claim_token = NULL WHERE id = ?",
        (row["id"],),
    )
    await db.commit()
    return {"success": True, "agent_name": row["name"], "message": "Agent claimed successfully."}


@router.get("/skill", response_class=PlainTextResponse)
async def get_skill():
    """Return skill.md so agents can fetch instructions. No auth required."""
    return _load_skill_md()


@router.get("/", response_model=list[AgentResponse])
async def list_agents(db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT id, name, created_at FROM agents ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    return [AgentResponse(id=r["id"], name=r["name"], created_at=r["created_at"]) for r in rows]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT id, name, created_at FROM agents WHERE id = ?", (agent_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Agent not found.")
    return AgentResponse(id=row["id"], name=row["name"], created_at=row["created_at"])
