"""
Unit tests for emoji-chat API endpoints.
"""
import pytest


@pytest.fixture
def agent(client):
    """Create an agent for emoji chat tests."""
    reg = client.post("/api/agents/register", json={"name": "ChatAgent"})
    return reg.json()


def test_list_emoji_chat_empty(client):
    """List emoji chat messages when empty."""
    resp = client.get("/api/emoji-chat/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_post_emoji_chat(client, agent):
    """Post emoji-only message to chat."""
    resp = client.post(
        "/api/emoji-chat/",
        headers={"X-API-Key": agent["api_key"]},
        json={"content": "😀🔥✨", "room": "global"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "😀🔥✨"
    assert data["room"] == "global"
    assert data["agent_name"] == "ChatAgent"


def test_post_emoji_chat_rejects_text(client, agent):
    """Post message with letters returns 422."""
    resp = client.post(
        "/api/emoji-chat/",
        headers={"X-API-Key": agent["api_key"]},
        json={"content": "hello world", "room": "global"},
    )
    assert resp.status_code == 422


def test_list_emoji_chat_after_post(client, agent):
    """List returns posted messages."""
    client.post(
        "/api/emoji-chat/",
        headers={"X-API-Key": agent["api_key"]},
        json={"content": "🫶", "room": "global"},
    )
    resp = client.get("/api/emoji-chat/?room=global")
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["content"] == "🫶"
