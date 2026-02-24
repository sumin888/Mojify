"""
Optional LLM-based emoji generator for instant Telegram responses.
Uses OpenAI when OPENAI_API_KEY is set; otherwise returns None.
"""

import os
from typing import Optional


async def generate_emoji_for_context(context: str) -> Optional[tuple[str, str]]:
    """
    Generate an emoji/emoticon string and rationale for the given conversation context.
    Returns (emoji_string, rationale) or None if no API key.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        import httpx
    except ImportError:
        return None

    system_prompt = """You are an expert at expressing emotions through emojis and emoticons.
Given a conversation snippet, suggest 1-2 emoji or emoticon strings that capture the perfect emotional response.
Use either Unicode emojis (😀🎉🙌) or classic emoticons (:), :D, \\o/, ^_^, etc.).
Output exactly two lines:
Line 1: The emoji/emoticon string only (no quotes, no explanation)
Line 2: A brief rationale (one short phrase)"""

    user_prompt = f"Conversation snippet:\n\n{context[:2000]}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 150,
                "temperature": 0.7,
            },
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            return None

        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            return None

        lines = [l.strip() for l in content.split("\n") if l.strip()]
        emoji_string = lines[0] if lines else "😊"
        rationale = lines[1] if len(lines) > 1 else "AI-suggested response"

        # Sanitize: ensure we have something copy-pasteable
        if not emoji_string:
            emoji_string = "😊"

        return (emoji_string, rationale)
