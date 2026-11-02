
#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./scripts/create_project.sh MyGame
#   ./scripts/create_project.sh --project MyGame
#
# Directory structure:
#   AIGenerated/
#   ├── agent/
#   │   ├── scripts/create_project.sh
#   │   └── templates/game.yml
#   └── MyGame/
#       ├── project.godot
#       └── game.yml

# Parse arguments
if [[ $# -eq 1 ]]; then
    PROJECT_NAME="$1"
elif [[ $# -eq 2 && "$1" == "--project" ]]; then
    PROJECT_NAME="$2"
else
    echo "Usage: $0 [--project] <ProjectName>" >&2
    exit 1
fi

# Validate project name
if [[ ! "$PROJECT_NAME" =~ ^[A-Za-z][A-Za-z0-9_-]*$ ]]; then
    echo "Error: Invalid project name: $PROJECT_NAME" >&2
    exit 1
fi

# Resolve directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

PROJECT_DIR="$BASE_DIR/$PROJECT_NAME"
GAME_TEMPLATE="$AGENT_DIR/templates/game.yml"

# Godot executable
GODOT_BIN="${GODOT_BIN:-/Applications/Godot.app/Contents/MacOS/Godot}"

if [[ ! -x "$GODOT_BIN" ]] && command -v godot >/dev/null 2>&1; then
    GODOT_BIN="$(command -v godot)"
fi

# Validate dependencies
if [[ ! -x "$GODOT_BIN" ]]; then
    echo "Error: Godot executable not found: $GODOT_BIN" >&2
    exit 1
fi

if [[ ! -f "$GAME_TEMPLATE" ]]; then
    echo "Error: Game template not found: $GAME_TEMPLATE" >&2
    exit 1
fi

if [[ -e "$PROJECT_DIR" ]]; then
    echo "Error: Project already exists: $PROJECT_DIR" >&2
    exit 1
fi

echo "Creating Godot project: $PROJECT_NAME"

# Create project directory
mkdir -p "$PROJECT_DIR"

# Create minimal project.godot
cat > "$PROJECT_DIR/project.godot" <<EOF
config_version=5

[application]

config/name="$PROJECT_NAME"
EOF

# Copy default game profile
cp "$GAME_TEMPLATE" "$PROJECT_DIR/game.yml"

# Initialize Godot project
echo "Initializing Godot..."
"$GODOT_BIN" --headless --editor --path "$PROJECT_DIR" --quit

echo ""
echo "Godot project created successfully!"
echo "Project:  $PROJECT_NAME"
echo "Location: $PROJECT_DIR"
echo "Profile:  $PROJECT_DIR/game.yml"
echo ""
echo "Next step: Customize game.yml before initializing gameplay."
