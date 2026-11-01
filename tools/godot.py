

import json
import os
import subprocess
import tempfile
from pathlib import Path

from agents import RunContextWrapper, function_tool
from core.context import GameContext


ALLOWED_PROJECT_SETTINGS = {
    "application/run/main_scene": "string",
    "application/config/name": "string",
    "display/window/size/mode": "int",
    "display/window/size/viewport_width": "int",
    "display/window/size/viewport_height": "int",
    "display/window/stretch/mode": "string",
    "display/window/stretch/aspect": "string",
}


@function_tool
def update_project_setting(
    ctx: RunContextWrapper[GameContext],
    setting: str,
    value: str,
) -> str:
    """Update an allowed Godot project setting.

    Args:
        setting: Full setting path, e.g. display/window/size/mode.
        value: New value, represented as a string.
    """
    value_type = ALLOWED_PROJECT_SETTINGS.get(setting)

    if value_type is None:
        return f"Setting not allowed: {setting}"

    try:
        if value_type == "int":
            typed_value = int(value)
        else:
            typed_value = value
    except ValueError:
        return f"Invalid value for {setting}: {value}"

    root = ctx.context.project_path.resolve()

    if setting == "application/run/main_scene":
        if not value.startswith("res://"):
            return "Main scene must start with res://"

        scene = (root / value[6:]).resolve()

        if not scene.is_relative_to(root) or not scene.is_file():
            return f"Main scene not found: {value}"

    if setting == "display/window/size/mode":
        if typed_value not in (0, 1, 2, 3, 4):
            return "Invalid window mode"

    if setting in (
        "display/window/size/viewport_width",
        "display/window/size/viewport_height",
    ):
        if not 320 <= typed_value <= 8192:
            return "Viewport dimension must be between 320 and 8192"

    if setting == "display/window/stretch/mode":
        if typed_value not in ("disabled", "canvas_items", "viewport"):
            return "Invalid stretch mode"

    if setting == "display/window/stretch/aspect":
        if typed_value not in ("ignore", "keep", "keep_width", "keep_height", "expand"):
            return "Invalid stretch aspect"

    godot_bin = os.getenv(
        "GODOT_BIN",
        "/Applications/Godot.app/Contents/MacOS/Godot",
    )

    script = f"""
extends SceneTree

func _initialize() -> void:
    var setting = {json.dumps(setting)}
    var value = {json.dumps(typed_value)}
    ProjectSettings.set_setting(setting, value)
    var err = ProjectSettings.save()
    if err != OK:
        push_error("Could not save project settings")
        quit(1)
        return
    quit(0)
"""

    script_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".gd",
            prefix="_agent_settings_",
            dir=root,
            delete=False,
            encoding="utf-8",
        ) as temp:
            temp.write(script)
            script_path = Path(temp.name)

        result = subprocess.run(
            [
                godot_bin,
                "--headless",
                "--path", str(root),
                "--script", str(script_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            return (
                f"Failed to update {setting}:\n"
                f"{result.stdout}\n{result.stderr}"
            )

        return f"Updated {setting} = {typed_value}"

    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Failed to update setting: {exc}"

    finally:
        if script_path is not None:
            script_path.unlink(missing_ok=True)



def _validate_project(project_path: Path) -> dict:
    project_path = project_path.resolve()

    if not (project_path / "project.godot").is_file():
        return {
            "success": False,
            "error": "Missing project.godot",
        }

    godot_bin = os.getenv(
        "GODOT_BIN",
        "/Applications/Godot.app/Contents/MacOS/Godot",
    )

    try:
        result = subprocess.run(
            [
                godot_bin,
                "--headless",
                "--path", str(project_path),
                "--editor",
                "--quit",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = result.stdout + "\n" + result.stderr

        errors = [
            line for line in output.splitlines()
            if any(token in line for token in (
                "ERROR:",
                "SCRIPT ERROR:",
                "Parse Error:",
            ))
        ]

        return {
            "success": result.returncode == 0 and not errors,
            "exit_code": result.returncode,
            "errors": errors,
            "output": output[-12000:],
        }

    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "success": False,
            "error": str(exc),
        }


@function_tool
def validate_project(
    ctx: RunContextWrapper[GameContext],
) -> str:
    """Validate the current Godot project."""
    import json

    result = _validate_project(ctx.context.project_path)
    return json.dumps(result)


@function_tool
def configure_input_action(
    ctx: RunContextWrapper[GameContext],
    action: str,
    key: str,
    replace_existing: bool = False,
) -> str:
    """Create or update a Godot keyboard input action.

    Args:
        action: Input action name, e.g. return_to_menu.
        key: Physical key name, e.g. Escape, W, Space, Left.
        replace_existing: Remove existing bindings before adding the key.
    """
    import re

    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", action):
        return "Invalid input action name"

    if not key or len(key) > 40:
        return "Invalid key name"

    project = ctx.context.project_path.resolve()

    if not (project / "project.godot").is_file():
        return "Godot project not found"

    godot_bin = os.getenv(
        "GODOT_BIN",
        "/Applications/Godot.app/Contents/MacOS/Godot",
    )

    # Embed values as escaped string literals.
    action_literal = json.dumps(action)
    key_literal = json.dumps(key)
    replace_literal = "true" if replace_existing else "false"

    script = f"""
extends SceneTree

func _initialize() -> void:
    var action_name: String = {action_literal}
    var key_name: String = {key_literal}
    var replace: bool = {replace_literal}

    var keycode: Key = OS.find_keycode_from_string(key_name)

    if keycode == KEY_NONE:
        push_error("Unknown key: " + key_name)
        quit(1)
        return

    var event := InputEventKey.new()
    event.physical_keycode = keycode

    var setting_name := "input/" + action_name

    var existing_events: Array[InputEvent] = []
    var deadzone: float = 0.5

    if ProjectSettings.has_setting(setting_name) and not replace:
        var existing: Dictionary = ProjectSettings.get_setting(
            setting_name
        )
        deadzone = existing.get("deadzone", 0.5)
        for existing_event in existing.get("events", []):
            if existing_event is InputEvent:
                existing_events.append(existing_event)

    for existing_event in existing_events:
        if existing_event is InputEventKey:
            if existing_event.physical_keycode == keycode:
                print("Key already configured")
                quit(0)
                return

    existing_events.append(event)

    ProjectSettings.set_setting(setting_name, {{
        "deadzone": deadzone,
        "events": existing_events,
    }})

    var err := ProjectSettings.save()

    if err != OK:
        push_error("Failed to save project.godot")
        quit(1)
        return

    print("Configured: " + action_name + " -> " + key_name)
    quit(0)
"""

    script_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".gd",
            prefix="_input_action_",
            dir=project,
            delete=False,
            encoding="utf-8",
        ) as temp:
            temp.write(script)
            script_path = Path(temp.name)

        result = subprocess.run(
            [
                godot_bin,
                "--headless",
                "--path", str(project),
                "--script", str(script_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout + "\n" + result.stderr

        if result.returncode != 0 or "SCRIPT ERROR:" in output:
            return f"Input configuration failed:\n{output}"

        return (
            f"Configured input action '{action}' "
            f"with physical key '{key}'.\n{output}"
        )

    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"Input configuration failed: {exc}"

    finally:
        if script_path is not None:
            script_path.unlink(missing_ok=True)