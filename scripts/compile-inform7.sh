#!/usr/bin/env bash
#
# Compile Inform 7 source to Glulx (.ulx) story file.
#
# Usage: ./scripts/compile-inform7.sh
#
# Requires: inform7 toolchain built from source (see README.md)
#   The full pipeline is: inform7 → Inform 6 → Glulx bytecode
#   This is orchestrated by the 'inbuild' tool.
#
# Environment variables:
#   INFORM7_HOME     — path to the inform repo root (auto-detected from
#                      INFORM7_COMPILER or inbuild on PATH)
#   INFORM7_COMPILER — path to the inform7 binary (legacy, used to find home)
#
# Output: game/dist/story.ulx

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROJECT_DIR="$PROJECT_ROOT/game/inform"
OUTPUT_DIR="$PROJECT_ROOT/game/dist"
OUTPUT_FILE="$OUTPUT_DIR/story.ulx"

mkdir -p "$OUTPUT_DIR" "$PROJECT_DIR/Build" "$PROJECT_DIR/Index"

# Ensure uuid.txt exists (required by inbuild)
if [ ! -f "$PROJECT_DIR/uuid.txt" ]; then
  uuidgen > "$PROJECT_DIR/uuid.txt"
fi

if [ ! -f "$PROJECT_DIR/Source/story.ni" ]; then
  echo "Error: Inform 7 source not found at $PROJECT_DIR/Source/story.ni"
  exit 1
fi

# Find the inform toolchain
INFORM_HOME=""

if [ -n "${INFORM7_HOME:-}" ]; then
  INFORM_HOME="$INFORM7_HOME"
elif [ -n "${INFORM7_COMPILER:-}" ]; then
  # Derive home from compiler path: .../inform/inform7/Tangled/inform7 → .../inform
  INFORM_HOME="$(cd "$(dirname "$INFORM7_COMPILER")/../../.." && pwd)"
elif command -v inbuild &>/dev/null; then
  INFORM_HOME="$(cd "$(dirname "$(command -v inbuild)")/../.." && pwd)"
elif command -v inform7 &>/dev/null; then
  INFORM_HOME="$(cd "$(dirname "$(command -v inform7)")/../.." && pwd)"
else
  echo "Error: Inform 7 toolchain not found."
  echo ""
  echo "Build from source (see README.md), then either:"
  echo "  1. Set INFORM7_HOME to the inform repo root"
  echo "  2. Set INFORM7_COMPILER to the inform7 binary path"
  echo "  3. Add inbuild or inform7 to your PATH"
  echo ""
  exit 1
fi

INBUILD="$INFORM_HOME/inbuild/Tangled/inbuild"
INTERNAL="$INFORM_HOME/inform7/Internal"

if [ ! -x "$INBUILD" ]; then
  echo "Error: inbuild not found at $INBUILD"
  echo "Is INFORM7_HOME correct? Currently: $INFORM_HOME"
  exit 1
fi

if [ ! -d "$INTERNAL" ]; then
  echo "Error: Internal resources not found at $INTERNAL"
  exit 1
fi

echo "Compiling Inform 7 source to Glulx..."
echo "  Toolchain: $INFORM_HOME"
echo "  Source:    $PROJECT_DIR/Source/story.ni"
echo "  Output:    $OUTPUT_FILE"

"$INBUILD" -internal "$INTERNAL" -build -project "$PROJECT_DIR"

# Copy output to dist directory
BUILD_OUTPUT="$PROJECT_DIR/Build/output.ulx"
if [ -f "$BUILD_OUTPUT" ]; then
  cp "$BUILD_OUTPUT" "$OUTPUT_FILE"
  SIZE=$(wc -c < "$OUTPUT_FILE" | tr -d ' ')
  echo "Compilation successful: $OUTPUT_FILE ($SIZE bytes)"
else
  echo "Error: Compiled output not found at $BUILD_OUTPUT"
  exit 1
fi
