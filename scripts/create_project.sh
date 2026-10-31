
#!/bin/bash

set -euo pipefail

# Usage: ./scripts/create_project.sh <ProjectName>

if [ $# -ne 1 ]; then
    echo "Usage: $0 <ProjectName>"
    exit 1
fi

PROJECT_NAME="$1"

# Validate project name
if [[ ! "$PROJECT_NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo "Error: Invalid project name: $PROJECT_NAME"
    exit 1
fi

# Script location: AIGenerated/agent/scripts/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Projects location: AIGenerated/
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# New project directory
PROJECT_DIR="$BASE_DIR/$PROJECT_NAME"

# Locate Godot executable
GODOT_BIN="${GODOT_BIN:-/Applications/Godot.app/Contents/MacOS/Godot}"

if command -v godot >/dev/null 2>&1; then
    GODOT_BIN="$(command -v godot)"
fi

if [ ! -x "$GODOT_BIN" ]; then
    echo "Error: Godot executable not found: $GODOT_BIN"
    exit 1
fi

# Prevent overwriting existing projects
if [ -e "$PROJECT_DIR" ]; then
    echo "Error: Project already exists: $PROJECT_DIR"
    exit 1
fi

echo "Creating Godot project: $PROJECT_NAME"

# Create project directory
mkdir -p "$PROJECT_DIR"

# Create project.godot
cat > "$PROJECT_DIR/project.godot" <<EOF
config_version=5

[application]

config/name="$PROJECT_NAME"
run/main_scene=""

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
EOF

# Initialize Godot project
echo "Initializing Godot project..."

"$GODOT_BIN" \
    --headless \
    --editor \
    --path "$PROJECT_DIR" \
    --quit

echo ""
echo "Godot project created successfully!"
echo "Project: $PROJECT_NAME"
echo "Location: $PROJECT_DIR"
