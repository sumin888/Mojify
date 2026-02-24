"""
Telegram bot integration for Mojify.
Forward a conversation snippet to the bot → get the perfect emoji response.
"""

import os
import uuid
import secrets
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx
from core.database import get_db, DB_PATH
import aiosqlite
from core.mojify_agent import generate_emoji_for_context

router = APIRouter(prefix="/telegram", tags=["telegram"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")  # optional: verify webhook
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
APP_URL = os.getenv("APP_URL", os.getenv("VITE_API_URL", "http://localhost:8000"))


async def _get_or_create_telegram_agent():
    """Get or create the MojifyBot agent used for Telegram-submitted proposals."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT id, api_key FROM agents WHERE name = ?", ("MojifyBot",)
        )
        row = await cur.fetchone()
        if row:
            return row["id"], row["api_key"]

        agent_id = str(uuid.uuid4())
        api_key = f"tg_{secrets.token_hex(24)}"
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """INSERT INTO agents (id, name, api_key, claim_token, claim_status, created_at)
               VALUES (?, ?, ?, ?, 'claimed', ?)""",
            (agent_id, "MojifyBot", api_key, None, now),
        )
        await db.commit()
        return agent_id, api_key


async def _create_prompt_and_proposal(context: str, emoji_string: str, rationale: str):
    """Create a prompt on Mojify and submit a proposal. Returns prompt_id."""
    agent_id, api_key = await _get_or_create_telegram_agent()
    prompt_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO prompts (id, created_by, title, context_text, media_type, media_url, status, created_at)
               VALUES (?, ?, ?, ?, 'text', NULL, 'open', ?)""",
            (prompt_id, agent_id, "Telegram: conversation snippet", context[:5000], now),
        )
        proposal_id = str(uuid.uuid4())
        await db.execute(
            """INSERT INTO proposals (id, prompt_id, agent_id, emoji_string, rationale, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (proposal_id, prompt_id, agent_id, emoji_string, rationale, now),
        )
        await db.commit()

    # Sync search index
    import asyncio
    from core.search import sync_search_index
    await asyncio.to_thread(sync_search_index)

    return prompt_id


async def _send_telegram_message(chat_id: int, text: str, parse_mode: str = "HTML"):
    if not TELEGRAM_BOT_TOKEN:
        return
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            },
        )


def _extract_text_from_update(update: dict) -> Optional[str]:
    """Extract conversation text from a Telegram update."""
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return None

    text = msg.get("text") or msg.get("caption") or ""
    if not text or not text.strip():
        return None

    return text.strip()


async def process_update(update: dict) -> bool:
    """Process a Telegram update. Returns True if handled."""
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return False

    chat_id = msg.get("chat", {}).get("id")
    if not chat_id:
        return False

    text = _extract_text_from_update(update)
    if not text:
        if msg.get("text", "").strip() == "/start":
            await _send_telegram_message(
                chat_id,
                "👋 <b>Mojify Bot</b>\n\n"
                "Forward or paste a conversation snippet and I'll suggest the perfect emoji response.\n\n"
                "Just send me any text and I'll mojify it! ✨",
            )
        return True

    try:
        result = await generate_emoji_for_context(text)
        if result:
            emoji_string, rationale = result
        else:
            emoji_string = "😊✨"
            rationale = "Suggested response (add OPENAI_API_KEY for AI-powered suggestions)"

        await _create_prompt_and_proposal(text, emoji_string, rationale)
        arena_url = FRONTEND_URL.rstrip("/")
        reply = (
            f"🎯 <b>Your mojified response:</b>\n\n"
            f"<code>{emoji_string}</code>\n\n"
            f"<i>{rationale}</i>\n\n"
            f"📋 Copy the emoji above! Also posted to the arena: {arena_url}"
        )
        await _send_telegram_message(chat_id, reply)
    except Exception as e:
        await _send_telegram_message(
            chat_id,
            f"❌ Something went wrong: {str(e)[:200]}\n\nTry again or check the arena.",
        )
    return True


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Telegram sends updates here. Set webhook: POST https://api.telegram.org/bot<TOKEN>/setWebhook?url=<APP_URL>/telegram/webhook
    """
    if not TELEGRAM_BOT_TOKEN:
        return JSONResponse({"ok": True})

    try:
        update = await request.json()
    except Exception:
        return JSONResponse({"ok": True})

    await process_update(update)
    return JSONResponse({"ok": True})


@router.get("/webhook")
async def telegram_webhook_get():
    """Telegram may send GET for verification; we use POST for updates."""
    return {"status": "ok", "telegram": "webhook endpoint"}
