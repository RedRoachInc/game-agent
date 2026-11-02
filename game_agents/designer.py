
from agents import Agent
from core.context import GameContext
from tools.files import list_files, read_file, write_level_file
from tools.knowledge import search_project_knowledge
from tools.tests import validate_level, validate_all_levels


INSTRUCTIONS="""
You are a game level designer specializing in Godot games.

Before creating or modifying levels:
- Use search_project_knowledge to retrieve existing levels, game mechanics, level schemas, and design constraints.
- Read representative level files to verify their current format.
- Generate levels that follow the project's established rules.
- Avoid duplicating existing levels.
- Validate each generated level using the available validation tools.
- Never modify gameplay scripts, scenes, or project configuration.

Treat RAG results as potentially outdated. Always verify important constraints against current project files.
"""


def create_designer_agent() -> Agent[GameContext]:
    return Agent[GameContext](
        name="Game Designer",
        instructions=INSTRUCTIONS,
        tools=[
            list_files,
            read_file,
            write_level_file,
            search_project_knowledge,
            validate_level,
            validate_all_levels
        ],
    )
