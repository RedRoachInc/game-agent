"""Interactive launcher with SQLite command history. Run: uv run launcher.py"""

import asyncio
from pathlib import Path

from dotenv import load_dotenv
from core.context import GameContext
from core.history import start, finish, recent
from orchestrator import GameOrchestrator
import subprocess

ROOT = Path(__file__).resolve().parent
PROJECTS_DIR = ROOT.parent


def choose(title: str, options: list[str]) -> str:
    if not options:
        raise ValueError(f"No options available for {title.lower()}")
    print(f"\n{title}:")
    for index, option in enumerate(options, 1):
        print(f"  {index}. {option}")
    while True:
        answer = input("Choose number [1]: ").strip()
        if not answer:
            return options[0]
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        print(f"Enter a number between 1 and {len(options)}.")


def find_projects() -> list[Path]:
    return sorted(
        (
            p
            for p in PROJECTS_DIR.iterdir()
            if p.is_dir() and (p / "project.godot").is_file()
        ),
        key=lambda p: p.name.casefold(),
    )



def create_project():
    name = input("Enter project name: ").strip()

    project_path = PROJECTS_DIR / name

    subprocess.run(
        [
            "bash",
            str(ROOT / "scripts" / "create_project.sh"),
            "--project",
            name,
        ],
        cwd=ROOT,
        check=True,
    )

    game_context = GameContext(
        project_name=name,
        project_path=project_path.resolve(),
    )

    return game_context




def choose_task(project: Path, agents: list[str]) -> tuple[str, str]:
    history = recent(str(project.resolve()))
    options = ["New task"]
    if history:
        options.append("Repeat a previous task")
        options.append("View command history")
    while True:
        action = choose("Task options", options)
        if action == "View command history":
            print(f"\nHistory for {project.name}:")
            for row in history:
                print(
                    f"  #{row['id']} [{row['status']}] {row['agent']}: {row['task'][:90]}"
                )
            continue
        if action == "Repeat a previous task":
            labels = [
                f"#{r['id']} [{r['status']}] {r['agent']}: {r['task'][:75]}"
                for r in history
            ]
            selected = history[labels.index(choose("Repeat which command", labels))]
            agent = (
                selected["agent"]
                if selected["agent"] in agents
                else choose("Select an agent", agents)
            )
            return agent, selected["task"]
        agent = choose(f"Select an agent for {project.name}", agents)
        task = input("\nEnter task:\n> ").strip()
        while not task:
            task = input("Task cannot be empty.\n> ").strip()
        return agent, task


async def main() -> None:
    # create_project()
    # return
    load_dotenv(ROOT / ".env")
    projects = find_projects()
    if not projects:
        raise RuntimeError(f"No Godot projects found next to {ROOT}")
    name = choose("Select a Godot project", [p.name for p in projects])
    project = next(p for p in projects if p.name == name)
    orchestrator = GameOrchestrator(project_path=project)
    agent, task = choose_task(project, sorted(orchestrator.agents))

    command_id = start(str(project.resolve()), agent, task)
    print(f"\nRunning command #{command_id}: {agent} on {project.name}...\n")
    try:
        result = await orchestrator.run(role=agent, task=task)
    except asyncio.CancelledError:
        finish(command_id, "interrupted", error="Execution cancelled")
        raise
    except KeyboardInterrupt:
        finish(command_id, "interrupted", error="Keyboard interrupt")
        raise
    except Exception as exc:
        finish(command_id, "failed", error=f"{type(exc).__name__}: {exc}")
        raise
    else:
        failed = isinstance(result, dict) and (
            result.get("status") in ("failed", "failed_qa", "error")
            or result.get("success") is False
        )
        finish(command_id, "failed" if failed else "completed", result=result)
        print("\n--- Agent result ---")
        print(result)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
    except Exception as exc:
        print(f"\nError: {exc}")
        raise SystemExit(1) from exc
