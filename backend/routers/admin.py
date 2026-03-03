import os
import secrets
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from core.database import get_db

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ── Credentials (override via env vars in production) ─────────────────────────

_ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "mojify")
_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "yfijom888")

# ── In-memory session store: token → expiry timestamp ─────────────────────────

_sessions: dict[str, float] = {}
_SESSION_TTL = 8 * 3600  # 8 hours


# ── Auth helpers ──────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


def _require_admin(x_admin_token: Optional[str] = Header(None)) -> str:
    if not x_admin_token:
        raise HTTPException(status_code=401, detail="Missing admin token")
    expiry = _sessions.get(x_admin_token)
    if expiry is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    if time.time() > expiry:
        del _sessions[x_admin_token]
        raise HTTPException(status_code=401, detail="Session expired")
    return x_admin_token


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/login")
async def admin_login(body: LoginRequest):
    if body.username != _ADMIN_USERNAME or body.password != _ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = secrets.token_hex(32)
    _sessions[token] = time.time() + _SESSION_TTL
    return {"token": token}


@router.post("/logout")
async def admin_logout(token: str = Depends(_require_admin)):
    _sessions.pop(token, None)
    return {"ok": True}


@router.get("/prompts")
async def list_prompts(token: str = Depends(_require_admin), db=Depends(get_db)):
    cursor = await db.execute(
        """
        SELECT p.id, p.title, p.context_text, p.status, p.created_at,
               COUNT(pr.id) AS proposal_count
        FROM prompts p
        LEFT JOIN proposals pr ON pr.prompt_id = p.id
        GROUP BY p.id
        ORDER BY p.created_at DESC
        """
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


@router.patch("/prompts/{prompt_id}/open")
async def open_prompt(
    prompt_id: str,
    token: str = Depends(_require_admin),
    db=Depends(get_db),
):
    cursor = await db.execute("SELECT id FROM prompts WHERE id = ?", (prompt_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Prompt not found")
    await db.execute("UPDATE prompts SET status = 'open' WHERE id = ?", (prompt_id,))
    await db.commit()
    cursor2 = await db.execute(
        """SELECT p.id, p.title, p.context_text, p.status, p.created_at,
                  COUNT(pr.id) AS proposal_count
           FROM prompts p
           LEFT JOIN proposals pr ON pr.prompt_id = p.id
           WHERE p.id = ?
           GROUP BY p.id""",
        (prompt_id,),
    )
    return dict(await cursor2.fetchone())


@router.patch("/prompts/{prompt_id}/close")
async def close_prompt(
    prompt_id: str,
    token: str = Depends(_require_admin),
    db=Depends(get_db),
):
    cursor = await db.execute("SELECT id FROM prompts WHERE id = ?", (prompt_id,))
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Prompt not found")
    await db.execute("UPDATE prompts SET status = 'closed' WHERE id = ?", (prompt_id,))
    await db.commit()
    cursor2 = await db.execute(
        """SELECT p.id, p.title, p.context_text, p.status, p.created_at,
                  COUNT(pr.id) AS proposal_count
           FROM prompts p
           LEFT JOIN proposals pr ON pr.prompt_id = p.id
           WHERE p.id = ?
           GROUP BY p.id""",
        (prompt_id,),
    )
    return dict(await cursor2.fetchone())
