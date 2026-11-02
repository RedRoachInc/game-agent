import argparse
import hashlib
from pathlib import Path

from rag.chunker import chunk_text
from rag.database import get_collection

SUPPORTED_EXTENSIONS = {
    ".gd",
    ".tscn",
    ".tres",
    ".json",
    ".md",
}

EXCLUDED_DIRS = {
    ".godot",
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
}

def project_id(project_path: Path) -> str:
    path = str(project_path.resolve())
    return hashlib.sha256(path.encode()).hexdigest()[:16]


def index_project(project_path: Path) -> None:
    project_path = project_path.resolve()
    
    if not(project_path / "project.godot").is_file():
        raise ValueError(f"Not a Godot project: {project_path}")
    
    collection = get_collection()
    pid = project_id(project_path)
    
    existing = collection.get(
        where={"project_id": pid},
        include=[]
    )
    
    if existing["ids"]:
        collection.delete(ids=existing["ids"])
        
    total_files = 0
    total_chunks = 0
    
    for path in sorted(project_path.rglob("*")):
        if not path.is_file():
            continue
        
        relative = path.relative_to(project_path)
        
       

        if any(
            part in EXCLUDED_DIRS
            for part in relative.parts
        ): continue
        
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        
        if path.stat().st_size > 1_000_000:
            print(f"Skipping large files: {relative}")
            continue
        
        try:
            content = path.read_text(encoding="utf-8")
        except:
            print(f"Skipping non-UTF-8 file: {relative}")
            continue
        
        chunks = chunk_text(content)
        
        if not chunks:
            continue
        
        ids = []
        documents = []
        metadatas = []
        
        for index, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(
                f"{pid}:{relative}:{index}".encode()
            ).hexdigest()
            
            ids.append(chunk_id)
            documents.append(chunk["text"])
            
            metadatas.append({
                "project_id": pid,
                "path": str(relative),
                "extension": path.suffix.lower(),
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"]
            })
        
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        total_files += 1
        total_chunks += len(chunks)
        
        print(f"Indexed {relative}: {len(chunks)} chunks")
        
    print()
    print(f"Project: {project_path.name}")
    print(f"Files: {total_files}")
    print(f"Chunks: {total_chunks}")
    print(f"Collection total: {collection.count()}")
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project_path", type=Path)
    args = parser.parse_args()
    index_project(args.project_path)