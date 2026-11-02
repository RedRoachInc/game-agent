
# Project Agent Instructions

## Source of Truth

Read `game.yaml` before planning or modifying this project.

Treat its requirements as authoritative unless the
user explicitly requests a change.

## General Rules

- Use Godot 4.7-compatible GDScript.
- Follow the architecture defined in game.yaml.
- Prefer reusable components over duplicated code.
- Inspect existing files before changing them.
- Do not overwrite unrelated functionality.
- Validate changes using Godot headless mode.

## Developer Agent

- Implement mechanics defined in game.yaml.
- Use typed GDScript where practical.
- Follow the declared directory structure.
- Configure input actions using project tools.
- Verify scene and script references.

## Designer Agent

- Follow the level schema and game mechanics.
- Generate increasingly difficult levels.
- Validate solvability and deadlocks.
- Do not modify gameplay code.

## QA Agent

- Run automated project validation.
- Check initialization acceptance criteria.
- Report failures with file paths and errors.
- Do not mark initialization complete if tests fail.

## Initialization

When the project is new:

1. Read game.yaml.
2. Inspect the current Godot project.
3. Identify missing systems.
4. Generate an implementation plan.
5. Implement the required systems.
6. Run quality checks.
7. Report completed and incomplete requirements.
