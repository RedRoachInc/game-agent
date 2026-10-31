
from pathlib import Path

from agents import RunContextWrapper, function_tool
from core.context import GameContext


def safe_path(context: GameContext, path: str) -> Path:
    root = context.project_path.resolve()

    if path.startswith("res://"):
        path = path[6:]

    if not path or Path(path).is_absolute():
        raise ValueError("Invalid relative path")

    target = (root / path).resolve()

    if not target.is_relative_to(root):
        raise ValueError("Path outside project")

    return target


@function_tool
def list_files(
    ctx: RunContextWrapper[GameContext],
    directory: str = ".",
) -> str:
    """List files in a Godot project directory."""
    root = ctx.context.project_path.resolve()
    path = root if directory == "." else safe_path(ctx.context, directory)

    if not path.is_dir():
        return "Directory not found"

    return "\n".join(
        p.name for p in sorted(path.iterdir())
        if p.name != ".godot"
    )


@function_tool
def read_file(
    ctx: RunContextWrapper[GameContext],
    path: str,
) -> str:
    """Read a file from the current Godot project."""
    target = safe_path(ctx.context, path)

    if not target.is_file():
        return f"File not found: {path}"

    return target.read_text(encoding="utf-8")


@function_tool
def write_file(
    ctx: RunContextWrapper[GameContext],
    path: str,
    content: str,
) -> str:
    """Create or update a Godot script, scene, resource or JSON file."""
    target = safe_path(ctx.context, path)

    allowed = {".gd", ".tscn", ".tres", ".json"}

    if target.suffix.lower() not in allowed:
        return f"Unsupported file type: {target.suffix}"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    return f"Saved: {path}"
