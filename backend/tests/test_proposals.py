"""
Unit tests for proposals API endpoints.
Requires agent auth (X-API-Key).
"""
import pytest


@pytest.fixture
def agent_and_prompt(client):
    """Create an agent and a prompt for proposal tests."""
    reg = client.post("/api/agents/register", json={"name": "ProposalAgent"})
    agent = reg.json()
    prompt = client.post(
        "/api/prompts/",
        json={"title": "Proposal test", "context_text": "context", "media_type": "text"},
    ).json()
    return {"agent": agent, "prompt": prompt}


def test_submit_proposal(client, agent_and_prompt):
    """Submit a proposal with valid API key."""
    agent = agent_and_prompt["agent"]
    prompt = agent_and_prompt["prompt"]
    resp = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        headers={"X-API-Key": agent["api_key"]},
        json={"emoji_string": "😀🔥✨", "rationale": "Happy and fire"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["emoji_string"] == "😀🔥✨"
    assert data["rationale"] == "Happy and fire"
    assert data["agent_name"] == "ProposalAgent"
    assert data["votes"] == 0


def test_submit_proposal_without_api_key(client, agent_and_prompt):
    """Submit proposal without API key returns 401 or 422."""
    prompt = agent_and_prompt["prompt"]
    resp = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        json={"emoji_string": "😀", "rationale": None},
    )
    assert resp.status_code in (401, 422)  # 401 from auth or 422 from FastAPI


def test_submit_proposal_invalid_api_key(client, agent_and_prompt):
    """Submit proposal with invalid API key returns 401."""
    prompt = agent_and_prompt["prompt"]
    resp = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        headers={"X-API-Key": "invalid-key"},
        json={"emoji_string": "😀", "rationale": None},
    )
    assert resp.status_code == 401


def test_submit_proposal_prompt_not_found(client, agent_and_prompt):
    """Submit proposal to non-existent prompt returns 404."""
    agent = agent_and_prompt["agent"]
    resp = client.post(
        "/api/prompts/nonexistent-uuid/proposals",
        headers={"X-API-Key": agent["api_key"]},
        json={"emoji_string": "😀", "rationale": None},
    )
    assert resp.status_code == 404


def test_submit_proposal_closed_prompt(client, agent_and_prompt):
    """Submit proposal to closed prompt returns 409."""
    agent = agent_and_prompt["agent"]
    prompt = agent_and_prompt["prompt"]
    client.patch(f"/api/prompts/{prompt['id']}/close")
    resp = client.post(
        f"/api/prompts/{prompt['id']}/proposals",
        headers={"X-API-Key": agent["api_key"]},
        json={"emoji_string": "😀", "rationale": None},
    )
    assert resp.status_code == 409
