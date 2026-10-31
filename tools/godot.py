

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

    script = """
extends SceneTree

func _initialize() -> void:
    var setting = %s
    var value = %s
    ProjectSettings.set_setting(setting, value)
    var err = ProjectSettings.save()
    if err != OK:
        push_error("Could not save project settings")
        quit(1)
        return
    quit(0)
""" % (
        json.dumps(setting),
        json.dumps(typed_value),
    )

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


# @function_tool
# def update_project_setting(
#     ctx: RunContextWrapper[GameContext],
#     setting: str,
#     value: str,
# ) -> str:
#     """Update an allowed Godot project setting.

#     Args:
#         setting: Godot setting path, e.g. application/run/main_scene.
#         value: Setting value as a string.
#     """
#     allowed_settings = {
#         "application/run/main_scene",
#         "application/config/name",
#     }

#     if setting not in allowed_settings:
#         return f"Setting not allowed: {setting}"

#     if setting == "application/run/main_scene":
#         if not value.startswith("res://"):
#             return "Main scene must use a res:// path"

#         relative_path = value.removeprefix("res://")
#         scene = (ctx.context.project_path / relative_path).resolve()
#         root = ctx.context.project_path.resolve()

#         if not scene.is_relative_to(root) or not scene.is_file():
#             return f"Scene not found: {value}"

#     try:
#         from pathlib import Path
#         import subprocess
#         import os

#         # Use Godot itself to modify project settings
#         script = '''
# extends SceneTree

# func _initialize():
#     ProjectSettings.set_setting(
#         "%s",
#         "%s"
#     )
#     ProjectSettings.save()
#     quit()
# ''' % (setting, value.replace("\\", "\\\\").replace('"', '\\"'))

#         script_path = ctx.context.project_path / "_update_settings.gd"

#         script_path.write_text(script, encoding="utf-8")

#         godot_bin = os.getenv(
#             "GODOT_BIN",
#             "/Applications/Godot.app/Contents/MacOS/Godot"
#         )

#         result = subprocess.run(
#             [
#                 godot_bin,
#                 "--headless",
#                 "--path",
#                 str(ctx.context.project_path),
#                 "--script",
#                 str(script_path),
#             ],
#             capture_output=True,
#             text=True,
#             timeout=30,
#         )

#         script_path.unlink(missing_ok=True)

#         if result.returncode != 0:
#             return f"Failed: {result.stderr}"

#         return f"Updated {setting} = {value}"

#     except Exception as error:
#         return f"Failed to update setting: {error}"
