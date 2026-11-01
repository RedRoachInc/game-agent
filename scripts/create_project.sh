
#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./create_project.sh
#   ./create_project.sh MyProject
#   ./create_project.sh --project MyProject --game "My Game" \
#     --team TEAMID1234 --bundle de.redroach.mygame
#
# Environment variables:
#   PROJECT_NAME
#   GAME_NAME
#   IOS_TEAM_ID
#   IOS_BUNDLE_ID
#   GODOT_BIN

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

SOURCE_ICON="$SCRIPT_DIR/AppIcon_iOS_1024.png"
GODOT_BIN="${GODOT_BIN:-/Applications/Godot.app/Contents/MacOS/Godot}"

PROJECT_NAME="${PROJECT_NAME:-}"
GAME_NAME="${GAME_NAME:-}"
TEAM_ID="${IOS_TEAM_ID:-}"
BUNDLE_ID="${IOS_BUNDLE_ID:-}"

DEFAULT_TEAM_ID="TUVC7XG5L7"
DEFAULT_BUNDLE_PREFIX="de.redroach"

# --------------------------------------------------
# Helpers
# --------------------------------------------------

usage() {
  cat <<EOF
Usage: $0 [ProjectName] [options]

Options:
  -p, --project NAME   Project directory name
  -g, --game NAME      Game display name
  -t, --team ID        Apple Developer Team ID
  -b, --bundle ID      iOS bundle identifier
  -h, --help           Show help

Missing values are requested interactively.

Environment variables:
  PROJECT_NAME
  GAME_NAME
  IOS_TEAM_ID
  IOS_BUNDLE_ID
  GODOT_BIN
EOF
}

error() {
  echo "Error: $*" >&2
  exit 1
}

prompt_value() {
  local label="$1"
  local default="${2:-}"
  local result

  if [[ ! -t 0 ]]; then
    [[ -n "$default" ]] || error \
      "Missing $label in non-interactive mode."
    printf '%s' "$default"
    return
  fi

  if [[ -n "$default" ]]; then
    read -r -p "$label [$default]: " result
    printf '%s' "${result:-$default}"
  else
    read -r -p "$label: " result
    printf '%s' "$result"
  fi
}

# --------------------------------------------------
# Parse arguments
# --------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--project)
      [[ $# -ge 2 ]] || error "Missing value for $1"
      PROJECT_NAME="$2"
      shift 2
      ;;

    -g|--game)
      [[ $# -ge 2 ]] || error "Missing value for $1"
      GAME_NAME="$2"
      shift 2
      ;;

    -t|--team)
      [[ $# -ge 2 ]] || error "Missing value for $1"
      TEAM_ID="$2"
      shift 2
      ;;

    -b|--bundle)
      [[ $# -ge 2 ]] || error "Missing value for $1"
      BUNDLE_ID="$2"
      shift 2
      ;;

    -h|--help)
      usage
      exit 0
      ;;

    -*)
      error "Unknown option: $1"
      ;;

    *)
      if [[ -z "$PROJECT_NAME" ]]; then
        PROJECT_NAME="$1"
      else
        error "Unexpected argument: $1"
      fi
      shift
      ;;
  esac
done

# --------------------------------------------------
# Prompt for missing values
# --------------------------------------------------

echo ""
echo "RedRoach AI - Godot Project Generator"
echo "===================================="
echo ""

if [[ -z "$PROJECT_NAME" ]]; then
  PROJECT_NAME="$(prompt_value "Project directory name")"
fi

[[ "$PROJECT_NAME" =~ ^[A-Za-z][A-Za-z0-9_-]*$ ]] || \
  error "Invalid project name: $PROJECT_NAME"

BUNDLE_SUFFIX="$(
  printf '%s' "$PROJECT_NAME" |
    tr '[:upper:]' '[:lower:]' |
    tr -cd 'a-z0-9'
)"

DEFAULT_BUNDLE_ID="${DEFAULT_BUNDLE_PREFIX}.${BUNDLE_SUFFIX}"

if [[ -z "$GAME_NAME" ]]; then
  GAME_NAME="$(prompt_value "Game display name" "$PROJECT_NAME")"
fi

if [[ -z "$TEAM_ID" ]]; then
  TEAM_ID="$(prompt_value "Apple Team ID" "$DEFAULT_TEAM_ID")"
fi

if [[ -z "$BUNDLE_ID" ]]; then
  BUNDLE_ID="$(prompt_value "iOS Bundle Identifier" "$DEFAULT_BUNDLE_ID")"
fi

# --------------------------------------------------
# Validate configuration
# --------------------------------------------------

[[ -n "$GAME_NAME" ]] || error "Game name cannot be empty."

[[ "$TEAM_ID" =~ ^[A-Za-z0-9]{10}$ ]] || \
  error "Invalid Apple Team ID: $TEAM_ID"

[[ "$BUNDLE_ID" =~ ^[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$ ]] || \
  error "Invalid bundle identifier: $BUNDLE_ID"

PROJECT_DIR="$BASE_DIR/$PROJECT_NAME"

[[ ! -e "$PROJECT_DIR" ]] || \
  error "Project already exists: $PROJECT_DIR"

if [[ ! -x "$GODOT_BIN" ]] && command -v godot >/dev/null 2>&1; then
  GODOT_BIN="$(command -v godot)"
fi

[[ -x "$GODOT_BIN" ]] || \
  error "Godot executable not found: $GODOT_BIN"

[[ -f "$SOURCE_ICON" ]] || \
  error "Missing icon: $SOURCE_ICON"

command -v sips >/dev/null || \
  error "macOS sips is required."

# Escape strings for Godot configuration files.
godot_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '%s' "$value"
}

GAME_NAME_ESCAPED="$(godot_escape "$GAME_NAME")"
PROJECT_NAME_ESCAPED="$(godot_escape "$PROJECT_NAME")"

# --------------------------------------------------
# Summary
# --------------------------------------------------

echo ""
echo "Configuration"
echo "-------------"
echo "Project:   $PROJECT_NAME"
echo "Game:      $GAME_NAME"
echo "Team ID:   $TEAM_ID"
echo "Bundle ID: $BUNDLE_ID"
echo "Location:  $PROJECT_DIR"
echo ""

# --------------------------------------------------
# Create directories
# --------------------------------------------------

mkdir -p \
  "$PROJECT_DIR/icons" \
  "$PROJECT_DIR/build/ios"

# --------------------------------------------------
# Generate icons
# --------------------------------------------------

echo "Generating icons..."

cp "$SOURCE_ICON" "$PROJECT_DIR/icons/icon_source.png"

sips -s format png -z 1024 1024 \
  "$SOURCE_ICON" \
  --out "$PROJECT_DIR/icons/icon.png" >/dev/null

for size in 40 58 60 76 80 87 120 152 167 180 1024; do
  sips -s format png -z "$size" "$size" \
    "$SOURCE_ICON" \
    --out "$PROJECT_DIR/icons/icon_${size}x${size}.png" \
    >/dev/null
done

# --------------------------------------------------
# Main scene
# --------------------------------------------------

cat > "$PROJECT_DIR/main.tscn" <<'EOF'
[gd_scene format=3]

[node name="Main" type="Node2D"]
EOF

# --------------------------------------------------
# Godot project configuration
# --------------------------------------------------

cat > "$PROJECT_DIR/project.godot" <<EOF
config_version=5

[application]

config/name="$GAME_NAME_ESCAPED"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("GL Compatibility")
config/icon="res://icons/icon.png"

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
textures/vram_compression/import_etc2_astc=true
EOF

# --------------------------------------------------
# iOS export preset
# --------------------------------------------------

cat > "$PROJECT_DIR/export_presets.cfg" <<EOF
[preset.0]

name="iOS"
platform="iOS"
runnable=true
advanced_options=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="build/ios/$PROJECT_NAME.xcodeproj"

[preset.0.options]

application/app_store_team_id="$TEAM_ID"
application/bundle_identifier="$BUNDLE_ID"

application/short_version="1.0"
application/version="1"

application/code_sign_identity_debug="Apple Development"
application/code_sign_identity_release="Apple Distribution"

application/provisioning_profile_uuid_debug=""
application/provisioning_profile_uuid_release=""

application/icon_interpolation=4

icons/icon_1024x1024="res://icons/icon_1024x1024.png"
icons/icon_180x180="res://icons/icon_180x180.png"
icons/icon_167x167="res://icons/icon_167x167.png"
icons/icon_152x152="res://icons/icon_152x152.png"
icons/icon_120x120="res://icons/icon_120x120.png"
icons/icon_87x87="res://icons/icon_87x87.png"
icons/icon_80x80="res://icons/icon_80x80.png"
icons/icon_76x76="res://icons/icon_76x76.png"
icons/icon_60x60="res://icons/icon_60x60.png"
icons/icon_40x40="res://icons/icon_40x40.png"
icons/settings_58x58="res://icons/icon_58x58.png"
EOF

# --------------------------------------------------
# Initialize Godot
# --------------------------------------------------

echo "Initializing Godot project..."

"$GODOT_BIN" \
  --headless \
  --editor \
  --path "$PROJECT_DIR" \
  --import \
  --quit

echo ""
echo "Godot project created successfully!"
echo ""
echo "Project:   $PROJECT_NAME"
echo "Game:      $GAME_NAME"
echo "Location:  $PROJECT_DIR"
echo "Team ID:   $TEAM_ID"
echo "Bundle ID: $BUNDLE_ID"
echo "ETC2/ASTC: enabled"
echo ""
echo "Open the project in Godot to continue development."

# --------------------------------------------------
# Ask to open project in Godot
# --------------------------------------------------

if [[ -t 0 ]]; then
  echo ""
  read -r -p "Open project in Godot now? [Y/n]: " OPEN_PROJECT

  if [[ ! "$OPEN_PROJECT" =~ ^[Nn]$ ]]; then
    echo "Opening $GAME_NAME in Godot..."

    "$GODOT_BIN" \
      --editor \
      --path "$PROJECT_DIR" \
      >/dev/null 2>&1 &
  fi
fi
