"""
Unit tests for leaderboard API endpoint.
"""
import pytest


def test_leaderboard_empty(client):
    """Leaderboard with no agents returns empty list."""
    resp = client.get("/api/leaderboard/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_leaderboard_with_agents(client):
    """Leaderboard returns agents with scores."""
    reg = client.post("/api/agents/register", json={"name": "LBAgent"})
    agent = reg.json()
    prompt = client.post(
        "/api/prompts/",
        json={"title": "LB test", "context_text": "x", "media_type": "text"},
    ).json()
    proposal = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        headers={"X-API-Key": agent["api_key"]},
        json={"emoji_string": "👍", "rationale": None},
    ).json()
    client.post(
        f"/api/proposals/{proposal['id']}/vote",
        json={"value": 1, "user_fingerprint": "u1"},
    )
    resp = client.get("/api/leaderboard/")
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) >= 1
    entry = next(e for e in entries if e["agent_name"] == "LBAgent")
    assert entry["total_score"] >= 1
    assert "win_rate" in entry
    assert "rank" in entry
