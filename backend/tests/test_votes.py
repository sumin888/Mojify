"""
Unit tests for votes API endpoints.
"""
import pytest


@pytest.fixture
def agent_prompt_proposal(client):
    """Create agent, prompt, and proposal for vote tests."""
    reg = client.post("/api/agents/register", json={"name": "VoteAgent"})
    agent = reg.json()
    prompt = client.post(
        "/api/prompts/",
        json={"title": "Vote test", "context_text": "x", "media_type": "text"},
    ).json()
    proposal = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        headers={"X-API-Key": agent["api_key"]},
        json={"emoji_string": "👍", "rationale": None},
    ).json()
    return {"proposal": proposal}


def test_vote_up(client, agent_prompt_proposal):
    """Upvote a proposal."""
    proposal_id = agent_prompt_proposal["proposal"]["id"]
    resp = client.post(
        f"/api/proposals/{proposal_id}/vote",
        json={"value": 1, "user_fingerprint": "user-1"},
    )
    assert resp.status_code == 200
    assert resp.json()["net_votes"] == 1


def test_vote_down(client, agent_prompt_proposal):
    """Downvote a proposal."""
    proposal_id = agent_prompt_proposal["proposal"]["id"]
    resp = client.post(
        f"/api/proposals/{proposal_id}/vote",
        json={"value": -1, "user_fingerprint": "user-2"},
    )
    assert resp.status_code == 200
    assert resp.json()["net_votes"] == -1


def test_vote_change(client, agent_prompt_proposal):
    """Change vote (upsert)."""
    proposal_id = agent_prompt_proposal["proposal"]["id"]
    client.post(
        f"/api/proposals/{proposal_id}/vote",
        json={"value": 1, "user_fingerprint": "user-3"},
    )
    resp = client.post(
        f"/api/proposals/{proposal_id}/vote",
        json={"value": -1, "user_fingerprint": "user-3"},
    )
    assert resp.status_code == 200
    assert resp.json()["net_votes"] == -1


def test_vote_proposal_not_found(client):
    """Vote on non-existent proposal returns 404."""
    resp = client.post(
        "/api/proposals/nonexistent-uuid/vote",
        json={"value": 1, "user_fingerprint": "user-1"},
    )
    assert resp.status_code == 404
