"""Read-only QA agent. Actual pass/fail must come from deterministic tools."""
from agents import Agent
from core.context import GameContext
from tools.files import list_files, read_file
from tools.godot import validate_project
from tools.tests import validate_level, validate_all_levels, run_project_tests

INSTRUCTIONS = """
You are a Godot 4 quality assurance engineer.

Read the project profile and inspect relevant files.
Use run_project_tests for the final QA result.
For Sokoban, use validate_level or validate_all_levels when appropriate.
Never create, overwrite, or delete project files.
Never claim that a test passed unless its tool output reports success=true.
Report every failed check, including unsupported formats and inconclusive solvers.
Do not publish or approve releases.

Final report:
- PASS or FAIL, based strictly on the tools
- Checks executed
- Errors and warnings
- Recommended fixes
"""


def create_qa_agent() -> Agent[GameContext]:
    return Agent[GameContext](
        name="Godot QA",
        instructions=INSTRUCTIONS,
        tools=[
            list_files,
            read_file,
            validate_project,
            validate_level,
            validate_all_levels,
            run_project_tests,
        ],
    )
