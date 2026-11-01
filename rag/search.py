
import argparse
from pathlib import Path

from rag.database import get_collection
from rag.indexer import project_id


def search_project(
    project_path: Path,
    query: str,
    limit: int = 5,
) -> list[dict]:
    collection = get_collection()

    pid = project_id(project_path)

    # First determine how many chunks this project has.
    existing = collection.get(
        where={"project_id": pid},
        include=[],
    )

    if not existing["ids"]:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(limit, len(existing["ids"])),
        where={"project_id": pid},
        include=["documents", "metadatas", "distances"],
    )

    matches = []

    for document, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        matches.append({
            "path": metadata["path"],
            "start_line": metadata["start_line"],
            "end_line": metadata["end_line"],
            "distance": distance,
            "content": document,
        })

    return matches


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("project_path", type=Path)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)

    args = parser.parse_args()

    matches = search_project(
        args.project_path,
        args.query,
        args.limit,
    )

    if not matches:
        print("No indexed content found.")

    for index, match in enumerate(matches, start=1):
        print(f"\n{'=' * 60}")
        print(f"Result #{index}")
        print(f"File: {match['path']}")
        print(
            f"Lines: {match['start_line']}-"
            f"{match['end_line']}"
        )
        print(f"Distance: {match['distance']:.4f}")
        print("-" * 60)
        print(match["content"])
