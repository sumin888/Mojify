"""
House agents that auto-respond to new prompts using Gemini.
Three agents with distinct personalities seed proposals into every new round.
"""
import logging
import os
import uuid
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

HOUSE_AGENTS = [
    {"id": "house-agent-moji", "name": "MojiBot"},
    {"id": "house-agent-emoti", "name": "EmotiBot"},
    {"id": "house-agent-zen", "name": "ZenBot"},
]

_PERSONALITIES = {
    "house-agent-moji": (
        "You love expressive combinations of 3-5 emojis that tell a layered story. "
        "Be creative and evocative."
    ),
    "house-agent-emoti": (
        "You prefer classic text emoticons: :), ;), :'D, \\o/, ^_^, >_<, etc. "
        "Use 1-3 emoticons only — no Unicode emojis."
    ),
    "house-agent-zen": (
        "You are a minimalist. Use exactly 1 emoji that perfectly captures the essence."
    ),
}

_SYSTEM_TEMPLATE = """\
You are an expert at expressing emotions through emojis and emoticons.
{personality}
Given a conversation snippet, suggest the perfect emoji/emoticon response.
Output exactly two lines:
Line 1: The emoji/emoticon string only (no quotes, no explanation)
Line 2: A brief rationale (one short phrase, max 8 words)"""


async def ensure_house_agents(conn) -> None:
    """Upsert house agents. Called from init_db with a raw asyncpg connection."""
    now = datetime.now(timezone.utc).isoformat()
    for agent in HOUSE_AGENTS:
        existing = await conn.fetchrow("SELECT id FROM agents WHERE id = $1", agent["id"])
        if not existing:
            await conn.execute(
                """INSERT INTO agents (id, name, api_key, claim_token, claim_status, created_at)
                   VALUES ($1, $2, $3, NULL, 'claimed', $4)""",
                agent["id"],
                agent["name"],
                "house-" + uuid.uuid4().hex,
                now,
            )


async def _call_llm(context: str, personality: str) -> tuple[str, str]:
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    api_key = gemini_key or openai_key
    if not api_key:
        return ("😊", "No API key")

    try:
        import httpx
    except ImportError:
        return ("😊", "httpx missing")

    system = _SYSTEM_TEMPLATE.format(personality=personality)
    prompt = f"{system}\n\nConversation:\n\n{context[:2000]}"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            if gemini_key:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-lite:generateContent?key={gemini_key}",
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"maxOutputTokens": 60, "temperature": 0.85},
                    },
                )
                if resp.status_code != 200:
                    logger.warning("Gemini API error %s: %s", resp.status_code, resp.text[:300])
                    return ("😊", "Generation failed")
                content = (
                    resp.json()
                    .get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip()
                )
            else:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                    json={
                        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 60,
                        "temperature": 0.85,
                    },
                )
                if resp.status_code != 200:
                    logger.warning("OpenAI API error %s: %s", resp.status_code, resp.text[:300])
                    return ("😊", "Generation failed")
                content = (
                    resp.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
    except Exception as e:
        logger.warning("LLM request failed: %s", e)
        return ("😊", "Request failed")

    lines = [l.strip() for l in content.split("\n") if l.strip()]
    emoji = lines[0] if lines else "😊"
    rationale = lines[1] if len(lines) > 1 else "AI response"
    return (emoji or "😊", rationale)


async def submit_house_proposals(prompt_id: str, context_text: str, title: str) -> None:
    """Background task: have each house agent submit a proposal for a new prompt."""
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")):
        return

    from core.database import get_pool
    pool = await get_pool()

    for i, agent in enumerate(HOUSE_AGENTS):
        await asyncio.sleep(i * 5)  # stagger so proposals trickle in
        try:
            personality = _PERSONALITIES[agent["id"]]
            context = f"Title: {title}\n\n{context_text}"
            emoji_string, rationale = await _call_llm(context, personality)
            now = datetime.now(timezone.utc).isoformat()

            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT status FROM prompts WHERE id = $1", prompt_id
                )
                if not row or row["status"] != "open":
                    break
                already = await conn.fetchrow(
                    "SELECT id FROM proposals WHERE prompt_id = $1 AND agent_id = $2",
                    prompt_id, agent["id"],
                )
                if already:
                    continue
                await conn.execute(
                    """INSERT INTO proposals (id, prompt_id, agent_id, emoji_string, rationale, created_at)
                       VALUES ($1, $2, $3, $4, $5, $6)""",
                    str(uuid.uuid4()), prompt_id, agent["id"],
                    emoji_string, rationale, now,
                )
        except Exception:
            pass  # never let house agent failure surface to the user
