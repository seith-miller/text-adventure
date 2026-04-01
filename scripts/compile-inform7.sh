#!/usr/bin/env bash
#
# Compile Inform 7 source to Glulx (.ulx) story file.
#
# Usage: ./scripts/compile-inform7.sh
#
# Requires: inform7 CLI (https://github.com/ganelson/inform)
#   Install via:
#     - macOS:  brew install inform7
#     - Linux:  build from source or use Docker (see below)
#     - Docker: docker run --rm -v "$PWD":/work ganelson/inform7 ...
#
# Output: game/dist/story.ulx

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE_FILE="$PROJECT_ROOT/game/inform/Source/story.ni"
OUTPUT_DIR="$PROJECT_ROOT/game/dist"
BUILD_DIR="$PROJECT_ROOT/game/inform/Build"

mkdir -p "$OUTPUT_DIR" "$BUILD_DIR"

if [ ! -f "$SOURCE_FILE" ]; then
  echo "Error: Inform 7 source not found at $SOURCE_FILE"
  exit 1
fi

# Try to find the inform7 compiler
if command -v inform7 &>/dev/null; then
  COMPILER="inform7"
elif command -v ni &>/dev/null; then
  COMPILER="ni"
elif command -v docker &>/dev/null; then
  COMPILER="docker"
else
  echo "Error: Inform 7 compiler not found."
  echo ""
  echo "Install one of the following:"
  echo "  1. inform7 CLI: https://github.com/ganelson/inform"
  echo "     macOS: brew install inform7"
  echo "     Linux: build from source (see README)"
  echo "  2. Docker: docker pull ganelson/inform7"
  echo ""
  exit 1
fi

echo "Compiling Inform 7 source to Glulx..."
echo "  Source: $SOURCE_FILE"
echo "  Output: $OUTPUT_DIR/story.ulx"

if [ "$COMPILER" = "docker" ]; then
  echo "  Using Docker-based compiler..."
  docker run --rm \
    -v "$PROJECT_ROOT/game/inform:/project" \
    ganelson/inform7 \
    inform7 -project /project -format=ulx
else
  echo "  Using $COMPILER..."
  $COMPILER -project "$PROJECT_ROOT/game/inform" -format=ulx
fi

# Copy output to dist directory
if [ -f "$BUILD_DIR/output.ulx" ]; then
  cp "$BUILD_DIR/output.ulx" "$OUTPUT_DIR/story.ulx"
  echo "Compilation successful: $OUTPUT_DIR/story.ulx"
elif [ -f "$BUILD_DIR/auto.ulx" ]; then
  cp "$BUILD_DIR/auto.ulx" "$OUTPUT_DIR/story.ulx"
  echo "Compilation successful: $OUTPUT_DIR/story.ulx"
else
  echo "Error: Compiled output not found in $BUILD_DIR"
  echo "  Checking for any .ulx files..."
  find "$BUILD_DIR" -name "*.ulx" 2>/dev/null || true
  exit 1
fi

echo "Done. Story file ready at $OUTPUT_DIR/story.ulx"
