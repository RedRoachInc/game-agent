
import json
from pathlib import Path

import yaml
from agents import Runner

from core.context import GameContext
from game_agents.developer import create_developer_agent
from game_agents.designer import create_designer_agent
from game_agents.qa import create_qa_agent


class GameOrchestrator:
    def __init__(
        self,
        project_path: Path,
        profile_path: Path,
    ):
        self.project_path = project_path.resolve()

        if not (self.project_path / "project.godot").is_file():
            raise ValueError("Invalid Godot project")

        with profile_path.open() as file:
            self.profile = yaml.safe_load(file)

        self.context = GameContext(
            project_name=self.project_path.name,
            project_path=self.project_path,
            profile=self.profile,
        )

        self.agents = {
            "developer": create_developer_agent(),
            "designer": create_designer_agent(),
            "qa": create_qa_agent(),
        }

    async def run(self, role: str, task: str):
        if role not in self.agents:
            raise ValueError(f"Unknown agent: {role}")

        agent = self.agents[role]

        prompt = (
            "Project profile:\n"
            + json.dumps(self.profile, indent=2)
            + "\n\nTask:\n"
            + task
        )

        result = await Runner.run(
            agent,
            prompt,
            context=self.context,
            max_turns=25,
        )

        return result.final_output
