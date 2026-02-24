"""
Unit tests for main app endpoints (root, health).
"""
import pytest


def test_root(client):
    """Root endpoint returns status ok."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "mojify-api"}


def test_health(client):
    """Health endpoint returns healthy."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}
