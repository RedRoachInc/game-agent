
import os
from pathlib import Path

import pytest

from rag.database import get_collection
from rag.search import search_project


PROJECT_PATH = Path(
    os.getenv("GODOT_TEST_PROJECT", "../Sokoban")
).resolve()


def test_database_contains_documents():
    collection = get_collection()

    assert collection.count() > 0, (
        "Vector database is empty. "
        "Run: uv run python -m rag.indexer ../Sokoban"
    )


def test_semantic_search_returns_results():
    results = search_project(
        project_path=PROJECT_PATH,
        query="Where is player movement implemented?",
        limit=3,
    )

    assert len(results) > 0


def test_search_returns_valid_metadata():
    results = search_project(
        project_path=PROJECT_PATH,
        query="How does box pushing work?",
        limit=3,
    )

    assert results, "No search results found"

    for result in results:
        assert "path" in result
        assert "content" in result
        assert "distance" in result
        assert result["start_line"] >= 1
        assert result["end_line"] >= result["start_line"]


@pytest.mark.parametrize(
    "query",
    [
        "Where is player movement implemented?",
        "How does box pushing work?",
        "Where are levels loaded?",
        "How is the win condition checked?",
    ],
)
def test_common_queries(query):
    results = search_project(
        project_path=PROJECT_PATH,
        query=query,
        limit=3,
    )

    assert results, f"No results for: {query}"
