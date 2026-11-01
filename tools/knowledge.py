from agents import RunContextWrapper, function_tool

from core.conext import GameContext
from rag.search import search_project

@function_tool
def search_project_knowledge(
    ctx: RunContextWrapper[GameContext],
    query: str,
) -> str:
    """Search indexed Godot source code for relevant context."""
    
    matches = search_project(
        project_path=ctx.context.project_path,
        query=query,
        limit=5
    )
    
    if not matches:
        return(
            "No results found. Index the project first "
            "using python -m rag.indexer."
        )
        
    sections = []
    
    for match in matches:
        sections.append(
            f"File: {match['path']}\n",
            f"Lines: {match['start_line']}-",
            f"{match['end_line']}\n",
            f"Code: {match['content']}"
        )
        
    return "\n\n---\n\n".join(sections)