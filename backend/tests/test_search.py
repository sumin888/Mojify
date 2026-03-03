"""
Tests for hybrid search: BM25 (FTS5) + vector similarity.
"""
import pytest

from core.search import (
    init_search_tables,
    sync_search_index,
    hybrid_search,
    index_one,
    delete_one,
)


class TestSearchIndex:
    """Search index initialization and sync."""

    def test_init_search_tables_creates_tables(self):
        """init_search_tables creates FTS5 and embeddings tables."""
        from tests.test_utils import TEST_DB_PATH

        init_search_tables(TEST_DB_PATH)
        import sqlite3

        conn = sqlite3.connect(TEST_DB_PATH)
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('search_fts','search_embeddings')"
        )
        tables = [r[0] for r in cur.fetchall()]
        conn.close()
        assert "search_fts" in tables
        assert "search_embeddings" in tables

    def test_sync_search_index_empty_db(self):
        """sync_search_index with empty DB indexes nothing."""
        from tests.test_utils import TEST_DB_PATH

        init_search_tables(TEST_DB_PATH)
        count = sync_search_index(TEST_DB_PATH, incremental=True)
        assert count == 0

    def test_sync_and_search_prompt(self, client):
        """Create prompt, sync, search finds it."""
        from tests.test_utils import TEST_DB_PATH

        # Create a prompt
        r = client.post(
            "/api/prompts/",
            json={
                "title": "When your code compiles",
                "context_text": "Friend asked about the bug fix",
                "media_type": "text",
            },
        )
        assert r.status_code == 201
        prompt_id = r.json()["id"]

        # Sync search index (full rebuild to ensure prompt is indexed)
        sync_search_index(TEST_DB_PATH, incremental=False)

        # Search
        results = hybrid_search("code compiles", limit=10, db_path=TEST_DB_PATH)
        assert len(results) >= 1
        found = next((r for r in results if r["entity_type"] == "prompt" and r["entity_id"] == prompt_id), None)
        assert found is not None
        assert "code" in (found.get("title") or "").lower() or "code" in (found.get("snippet") or "").lower()

    def test_search_api_endpoint(self, client):
        """GET /api/search returns results."""
        from tests.test_utils import TEST_DB_PATH

        # Create prompt and sync
        client.post(
            "/api/prompts/",
            json={"title": "Happy birthday party", "context_text": "Celebration with cake", "media_type": "text"},
        )
        sync_search_index(TEST_DB_PATH, incremental=False)

        r = client.get("/api/search", params={"q": "birthday"})
        assert r.status_code == 200
        data = r.json()
        assert "query" in data
        assert data["query"] == "birthday"
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_empty_query_returns_empty(self, client):
        """Empty or whitespace query returns empty results."""
        from tests.test_utils import TEST_DB_PATH

        assert hybrid_search("", db_path=TEST_DB_PATH) == []
        assert hybrid_search("   ", db_path=TEST_DB_PATH) == []

    def test_search_intent_trending_returns_prompts(self, client):
        """Query 'trending' triggers intent path and returns prompts."""
        client.post("/api/prompts/", json={"title": "Trending round", "context_text": "votes", "media_type": "text"})
        r = client.get("/api/search", params={"q": "trending"})
        assert r.status_code == 200
        data = r.json()
        assert data["query"] == "trending"
        assert isinstance(data["results"], list)
        # All results should be prompt type (intent path only returns prompts)
        for result in data["results"]:
            assert result["entity_type"] == "prompt"

    def test_search_intent_new_returns_prompts(self, client):
        """Query 'new' triggers intent path and returns prompts sorted newest first."""
        client.post("/api/prompts/", json={"title": "First round", "context_text": "a", "media_type": "text"})
        client.post("/api/prompts/", json={"title": "Second round", "context_text": "b", "media_type": "text"})
        r = client.get("/api/search", params={"q": "new"})
        assert r.status_code == 200
        results = r.json()["results"]
        assert len(results) >= 2
        # Second (more recently created) should appear before first
        titles = [res["title"] for res in results]
        assert titles.index("Second round") < titles.index("First round")

    def test_search_prefix_matching(self, client):
        """Partial word 'age' should match 'agents' via FTS5 prefix query."""
        from tests.test_utils import TEST_DB_PATH
        client.post("/api/agents/register", json={"name": "PrefixSearchAgent"})
        sync_search_index(TEST_DB_PATH, incremental=False)
        r = client.get("/api/search", params={"q": "age"})
        assert r.status_code == 200
        results = r.json()["results"]
        found = any("agent" in res.get("title", "").lower() or "agent" in res.get("snippet", "").lower()
                    for res in results)
        assert found, "Prefix 'age' should match 'PrefixSearchAgent'"

    def test_index_one_and_delete_one(self):
        """index_one and delete_one work for single entities."""
        from tests.test_utils import TEST_DB_PATH

        init_search_tables(TEST_DB_PATH)
        index_one("prompt", "test-123", "Test title", "Test content for search", db_path=TEST_DB_PATH)

        results = hybrid_search("Test content", limit=5, db_path=TEST_DB_PATH)
        assert any(r["entity_id"] == "test-123" for r in results)

        delete_one("prompt", "test-123", db_path=TEST_DB_PATH)
        results_after = hybrid_search("Test content", limit=5, db_path=TEST_DB_PATH)
        assert not any(r["entity_id"] == "test-123" for r in results_after)
