from agents import Agent

from core.context import GameContext
from tools.files import list_files, read_file, write_file
from tools.godot import configure_input_action, update_project_setting, validate_project

INSTRUCTIONS="""
You are a senior Godot 4 game developer.

Responsibilities:
- Implement requested game features.
- Create and modify GDScript files.
- Create and modify Godot scenes.
- Follow the project's architecture and game profile.
- Preserve existing functionality.
- Validate all changes.

Rules:
- Inspect existing files before modifying them.
- Use typed GDScript.
- Never modify unrelated files.
- Never claim success without verification.
- Do not publish releases.
"""

def create_developer_agent() -> Agent[GameContext]:
    return Agent[GameContext](
        name="Godot Developer",
        instructions=INSTRUCTIONS,
        tools=[
            list_files,
            read_file,
            write_file,
            validate_project,
            update_project_setting,
            configure_input_action
        ]
    )
