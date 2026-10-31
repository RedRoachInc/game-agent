
import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from orchestrator import GameOrchestrator

load_dotenv()

ROOT = Path(__file__).resolve().parent
PROJECTS_DIR = ROOT.parent


async def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("project")
    parser.add_argument("--profile", default="sokoban")
    parser.add_argument(
        "--agent",
        choices=["developer", "designer", "qa"],
        default="developer",
    )
    parser.add_argument("--task", required=True)

    args = parser.parse_args()

    project_path = (PROJECTS_DIR / args.project).resolve()

    if project_path.parent != PROJECTS_DIR.resolve():
        parser.error("Invalid project name")

    profile_path = ROOT / "profiles" / f"{args.profile}.yaml"

    orchestrator = GameOrchestrator(
        project_path=project_path,
        profile_path=profile_path,
    )

    result = await orchestrator.run(
        role=args.agent,
        task=args.task,
    )

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
