"""Deterministic project and Sokoban-level checks for AI game agents."""
import json
from collections import deque
from pathlib import Path

from agents import RunContextWrapper, function_tool
from core.context import GameContext
from tools.godot import _validate_project

WALL = {"#", "wall"}
FLOOR = {" ", ".", "floor", "ground"}
PLAYER = {"@", "+", "player", "player_on_goal"}
BOX = {"$", "*", "box", "box_on_goal"}
GOAL = {".", "+", "*", "goal", "target", "player_on_goal", "box_on_goal"}


def _result(name: str, success: bool, errors=None, warnings=None, **extra) -> dict:
    return {"check": name, "success": success,
            "errors": errors or [], "warnings": warnings or [], **extra}


def _within(root: Path, relative: str) -> Path:
    if not relative or relative.startswith("res://"):
        relative = relative.removeprefix("res://")
    p = Path(relative)
    if p.is_absolute():
        raise ValueError("Absolute paths are not permitted")
    target = (root / p).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Path escapes project directory")
    return target


def _decode_level(data: dict):
    """Support ASCII rows, tile rows, and explicit wall/box/goal positions."""
    grid = data.get("grid", data.get("map"))
    if grid is None:
        raise ValueError("Unsupported level layout: expected 'grid' or 'map' rows")
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list of rows")
    rows = []
    for row in grid:
        if isinstance(row, str):
            rows.append(list(row))
        elif isinstance(row, list) and all(isinstance(x, str) for x in row):
            rows.append(row)
        else:
            raise ValueError("Each grid row must be a string or list of tile strings")
    width = len(rows[0])
    if width == 0 or any(len(row) != width for row in rows):
        raise ValueError("Grid rows must have equal, nonzero width")
    if len(rows) * width > 10000:
        raise ValueError("Grid is too large")
    walls, goals, boxes, players = set(), set(), set(), []
    allowed = WALL | FLOOR | PLAYER | BOX | GOAL
    for y, row in enumerate(rows):
        for x, token in enumerate(row):
            if token not in allowed:
                raise ValueError(f"Unknown tile {token!r} at ({x},{y})")
            point = (x, y)
            if token in WALL:
                walls.add(point)
            if token in GOAL:
                goals.add(point)
            if token in BOX:
                boxes.add(point)
            if token in PLAYER:
                players.append(point)
    if len(players) != 1:
        raise ValueError(f"Expected one player, found {len(players)}")
    if not boxes or len(boxes) != len(goals):
        raise ValueError(f"Boxes ({len(boxes)}) must equal goals ({len(goals)}) and be nonzero")
    return width, len(rows), walls, goals, frozenset(boxes), players[0]


def _solve(width, height, walls, goals, boxes, player, max_states=100000):
    """Breadth-first Sokoban solver; returns True, False, or None if search limit reached."""
    def valid(p):
        return 0 <= p[0] < width and 0 <= p[1] < height and p not in walls

    def reachable(start, blocks):
        seen = {start}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                nxt = (x + dx, y + dy)
                if valid(nxt) and nxt not in blocks and nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        return seen

    def dead_square(p):
        if p in goals:
            return False
        x, y = p
        return (not valid((x - 1, y)) or not valid((x + 1, y))) and (
            not valid((x, y - 1)) or not valid((x, y + 1))
        )

    if boxes == goals:
        return True, 0
    if any(dead_square(b) for b in boxes):
        return False, 0
    queue = deque([(player, boxes)])
    visited = set()
    explored = 0
    while queue:
        pos, state = queue.popleft()
        area = reachable(pos, state)
        key = (min(area), state)
        if key in visited:
            continue
        visited.add(key)
        explored += 1
        if explored > max_states:
            return None, explored
        for bx, by in state:
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                behind = (bx - dx, by - dy)
                ahead = (bx + dx, by + dy)
                if behind not in area or not valid(ahead) or ahead in state:
                    continue
                new_boxes = frozenset((state - {(bx, by)}) | {ahead})
                if new_boxes == goals:
                    return True, explored
                if dead_square(ahead):
                    continue
                queue.append(((bx, by), new_boxes))
    return False, explored


def check_level(project_path: Path, relative_path: str,
                profile: dict | None = None, max_states: int = 100000) -> dict:
    """Validate JSON and, for supported Sokoban grids, solve the level."""
    root = project_path.resolve()
    try:
        path = _within(root, relative_path)
        levels_dir = (root / (profile or {}).get("levels", {}).get("directory", "levels")).resolve()
        if not path.is_relative_to(levels_dir) or path.suffix.lower() != ".json":
            raise ValueError("Level must be a JSON file inside the configured levels directory")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("Level JSON root must be an object")
        if (profile or {}).get("levels", {}).get("generator") != "sokoban":
            return _result("level", False, ["No deterministic validator for this game profile"])
        width, height, walls, goals, boxes, player = _decode_level(data)
        solved, explored = _solve(width, height, walls, goals, boxes, player, max_states)
        if solved is None:
            return _result("level", False, ["Solver search limit reached; solvability unverified"],
                           states_explored=explored)
        return _result("level", bool(solved),
                       [] if solved else ["No solution found (or a static deadlock detected)"],
                       width=width, height=height, boxes=len(boxes),
                       states_explored=explored)
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        return _result("level", False, [str(exc)])


def check_all_levels(project_path: Path, profile: dict) -> dict:
    root = project_path.resolve()
    try:
        directory = _within(root, profile.get("levels", {}).get("directory", "levels"))
        if not directory.is_dir():
            return _result("levels", False, [f"Level directory not found: {directory}"])
        paths = sorted(directory.glob("*.json"))
        if not paths:
            return _result("levels", False, ["No JSON levels found"])
        checks = [check_level(root, str(p.relative_to(root)), profile) for p in paths]
        seen = {}
        for path in paths:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                grid = data.get("grid", data.get("map"))
                if grid is None:
                    continue
                key = json.dumps(grid, sort_keys=True)
                if key in seen:
                    checks[paths.index(path)]["success"] = False
                    checks[paths.index(path)]["errors"].append(
                        f"Duplicate grid: {seen[key].name}"
                    )
                else:
                    seen[key] = path
            except (ValueError, OSError):
                pass  # Already reported by check_level.
        return _result("levels", all(c["success"] for c in checks),
                       [f"{p.name}: {e}" for p, c in zip(paths, checks)
                        for e in c["errors"]],
                       files=[{"path": p.name, **c} for p, c in zip(paths, checks)])
    except (OSError, ValueError, TypeError) as exc:
        return _result("levels", False, [str(exc)])


def run_quality_checks(context: GameContext) -> dict:
    """Host-side QA gate; never trusts the model's self-assessment."""
    godot = _validate_project(context.project_path)
    checks = [{"check": "godot", **godot}]
    if context.profile.get("levels", {}).get("generator") == "sokoban":
        checks.append(check_all_levels(context.project_path, context.profile))
    return {"success": all(c["success"] for c in checks), "checks": checks}


@function_tool
def validate_level(ctx: RunContextWrapper[GameContext], path: str) -> str:
    """Validate a Sokoban level JSON and test whether it can be solved."""
    return json.dumps(check_level(ctx.context.project_path, path, ctx.context.profile))


@function_tool
def validate_all_levels(ctx: RunContextWrapper[GameContext]) -> str:
    """Validate all levels for the active profile and detect duplicate grids."""
    return json.dumps(check_all_levels(ctx.context.project_path, ctx.context.profile))


@function_tool
def run_project_tests(ctx: RunContextWrapper[GameContext]) -> str:
    """Run deterministic Godot and game-specific QA checks."""
    return json.dumps(run_quality_checks(ctx.context))
