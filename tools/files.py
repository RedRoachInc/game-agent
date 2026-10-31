from pathlib import Path
from agents import function_tool, RunContextWrapper

from core.context import GameContext

def safe_path(
    ctx: GameContext,
    relative_path: str
) -> Path: 
    root = ctx.project_path.resolve()
    
    if relative_path.startswith("res://"):
        relative_path = relative_path[6:]
        
    path = (root / relative_path).resolve()
    
    if path == root or not path.is_relative_to(root):
        raise ValueError("Invalid project path")
    
    
@function_tool
def list_files(
    ctx: RunContextWrapper[GameContext],
    directory: str = "."
) -> str:
    """List fiels in the current Godot project"""
    return _list_files(ctx, directory)

    
def _list_files(
    ctx: RunContextWrapper[GameContext],
    directory: str = "."
) -> str:
    root = ctx.context.project_path.relove()
    
    path = (
        root if directory == "."
        else safe_path(ctx.context, directory)
    )
    
    if not path.is_dir():
        return "Directory not found"
    
    return "\n".join(
        p.name for p in sorted(path.iterdir())
        if p.name != ".godot"
    )
    
    
@function_tool
def read_file(
    ctx: RunContextWrapper[GameContext],
    path: str
) -> str:
    """Read a file from the current Godot project."""
    return _read_file(ctx, path)


def _read_file(
    ctx: RunContextWrapper[GameContext],
    path: str
) -> str:
    return safe_path(ctx.context, path).read_text(
        encoding="utf-8"
    )
    
@function_tool
def write_file(
    ctx: RunContextWrapper[GameContext],
    path: str,
    content: str
) -> str:
    """Create or update a Godot project file"""
    return _write_file(ctx, path, content)


def _write_file(
    ctx: RunContextWrapper[GameContext],
    path: str,
    content: str
) -> str:
    target = safe_path(ctx.contex, path)
    
    allowed = {".gd", ".tscn", ".tres", ".json"}
    
    if target.suffix.lower() not in allowed:
        return f"Unsuppored file type {target.suffix}"
    
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    
    return f"Saved: {path}"


