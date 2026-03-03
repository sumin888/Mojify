"""
Tests for the Telegram integration endpoints.
TELEGRAM_BOT_TOKEN is not set in the test environment, so we test the
"no token" code paths and the webhook/process_update logic.
"""
import pytest
from unittest.mock import AsyncMock, patch


# ── Webhook endpoints ──────────────────────────────────────────────────────────

def test_telegram_webhook_get(client):
    """GET /telegram/webhook returns ok status."""
    resp = client.get("/telegram/webhook")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_telegram_webhook_post_no_token(client):
    """POST /telegram/webhook without bot token still returns ok (silently ignores)."""
    resp = client.post("/telegram/webhook", json={"update_id": 1, "message": {"text": "hi"}})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_telegram_webhook_post_invalid_json(client):
    """POST /telegram/webhook with bad body still returns ok."""
    resp = client.post("/telegram/webhook", content=b"not-json", headers={"content-type": "text/plain"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


# ── /telegram/info ─────────────────────────────────────────────────────────────

def test_telegram_info_no_token(client):
    """GET /telegram/info without TELEGRAM_BOT_TOKEN returns error dict (not 5xx)."""
    import routers.telegram as tg_module
    original = tg_module.TELEGRAM_BOT_TOKEN
    tg_module.TELEGRAM_BOT_TOKEN = None
    try:
        resp = client.get("/telegram/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is False
        assert "TELEGRAM_BOT_TOKEN" in data.get("error", "")
    finally:
        tg_module.TELEGRAM_BOT_TOKEN = original


def test_telegram_setup_no_token(client):
    """GET /telegram/setup without token returns error dict."""
    import routers.telegram as tg_module
    original = tg_module.TELEGRAM_BOT_TOKEN
    tg_module.TELEGRAM_BOT_TOKEN = None
    try:
        resp = client.get("/telegram/setup")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is False
    finally:
        tg_module.TELEGRAM_BOT_TOKEN = original


# ── process_update unit tests ──────────────────────────────────────────────────

def test_process_update_no_message(client):
    """Updates without a message field are handled gracefully."""
    import asyncio
    from routers.telegram import process_update
    result = asyncio.run(process_update({"update_id": 99}))
    assert result is False


def test_process_update_start_command(client):
    """The /start command is handled without calling the LLM."""
    import asyncio
    from unittest.mock import AsyncMock, patch
    from routers.telegram import process_update

    update = {
        "message": {
            "chat": {"id": 123},
            "text": "/start",
        }
    }
    with patch("routers.telegram._send_telegram_message", new_callable=AsyncMock) as mock_send:
        result = asyncio.run(process_update(update))
    assert result is True
    # Should send welcome message, not call LLM
    mock_send.assert_called_once()
    call_text = mock_send.call_args[0][1]
    assert "Mojify Bot" in call_text or "mojify" in call_text.lower()


def test_process_update_slash_command_not_sent_to_llm(client):
    """/unknown commands are handled and never reach the LLM."""
    import asyncio
    from routers.telegram import process_update

    update = {
        "message": {
            "chat": {"id": 456},
            "text": "/unknowncommand",
        }
    }
    with patch("routers.telegram.generate_emoji_for_context", new_callable=AsyncMock) as mock_llm, \
         patch("routers.telegram._send_telegram_message", new_callable=AsyncMock):
        result = asyncio.run(process_update(update))
    assert result is True
    mock_llm.assert_not_called()


def test_process_update_empty_text(client):
    """Messages with no text return True (handled) but do nothing."""
    import asyncio
    from routers.telegram import process_update

    update = {
        "message": {
            "chat": {"id": 789},
            # no text key
        }
    }
    result = asyncio.run(process_update(update))
    assert result is True
