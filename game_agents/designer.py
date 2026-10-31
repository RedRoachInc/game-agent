
from agents import Agent
from core.context import GameContext
from tools.files import list_files, read_file, write_file

INSTRUCTIONS="""
You are a professional game and level designer.

Responsibilities:
- Design gameplay mechanics.
- Create levels appropriate to the game profile.
- Maintain difficulty progression.
- Avoid repetitive content.
- Respect existing game rules.

Read the supplied game profile before designing.

Do not modify game engine code.
Only write level data files.

All generated levels must be validated
before being accepted.
"""


def create_designer_agent() -> Agent[GameContext]:
    return Agent[GameContext](
        name="Game Designer",
        instructions=INSTRUCTIONS,
        tools=[
            list_files,
            read_file,
            write_file,
        ],
    )
