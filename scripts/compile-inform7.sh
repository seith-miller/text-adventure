#!/usr/bin/env bash
#
# Compile Inform 7 source to Glulx (.ulx) story file.
#
# Uses the Inform 7 v10.1.2 `ni` compiler + inform6, taken from the
# Inform 7 macOS IDE (TobyLobster release 1.82.3). This is pinned to a
# stable tagged release because the master-branch inform7/inbuild at
# v10.2.0 is non-deterministically broken (produces "Parse tree broken"
# internal errors on the same source across repeated builds).
#
# Usage: ./scripts/compile-inform7.sh
#
# Environment:
#   INFORM7_STABLE_HOME — path to the stable compiler install (default:
#                         /Users/seithmiller/Code/inform-stable). Expected
#                         layout:
#                           <HOME>/ni
#                           <HOME>/inform6
#                           <HOME>/Internal/
#
# Output: game/dist/story.ulx
#
# To install the stable compiler (one-time):
#   1. Download https://github.com/TobyLobster/Inform/releases (latest DMG)
#   2. Open the .dmg and mount Inform.app
#   3. Copy binaries + resources:
#        cp /Volumes/Inform/Inform.app/Contents/MacOS/ni       $HOME/ni
#        cp /Volumes/Inform/Inform.app/Contents/MacOS/inform6  $HOME/inform6
#        cp -R /Volumes/Inform/Inform.app/Contents/Resources/Internal $HOME/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROJECT_DIR="$PROJECT_ROOT/game/inform"
SOURCE_FILE="$PROJECT_DIR/Source/story.ni"
OUTPUT_DIR="$PROJECT_ROOT/game/dist"
OUTPUT_FILE="$OUTPUT_DIR/story.ulx"
BUILD_DIR="$PROJECT_DIR/Build"

STABLE_HOME="${INFORM7_STABLE_HOME:-/Users/seithmiller/Code/inform-stable}"
NI_BIN="$STABLE_HOME/ni"
I6_BIN="$STABLE_HOME/inform6"
INTERNAL="$STABLE_HOME/Internal"

if [ ! -x "$NI_BIN" ] || [ ! -x "$I6_BIN" ] || [ ! -d "$INTERNAL" ]; then
  echo "Error: Stable Inform 7 toolchain not found at $STABLE_HOME"
  echo "See the header of this script for installation instructions."
  exit 1
fi

if [ ! -f "$SOURCE_FILE" ]; then
  echo "Error: Inform 7 source not found at $SOURCE_FILE"
  exit 1
fi

mkdir -p "$OUTPUT_DIR" "$BUILD_DIR" "$PROJECT_DIR/Index"

# Ensure uuid.txt exists (required by ni)
if [ ! -f "$PROJECT_DIR/uuid.txt" ]; then
  uuidgen > "$PROJECT_DIR/uuid.txt"
fi

echo "Compiling Inform 7 source to Glulx..."
echo "  Toolchain: $STABLE_HOME"
echo "  Source:    $SOURCE_FILE"
echo "  Output:    $OUTPUT_FILE"

# Stage 1: ni translates I7 → I6 source
"$NI_BIN" -format=Inform6/32d/v3.1.2 -internal "$INTERNAL" -project "$PROJECT_DIR"

# Stage 2: inform6 compiles I6 → Glulx bytecode
AUTO_INF="$BUILD_DIR/auto.inf"
if [ ! -f "$AUTO_INF" ]; then
  echo "Error: ni did not produce auto.inf (translation failed)"
  exit 1
fi

"$I6_BIN" -kE2SDwG "$AUTO_INF" "$BUILD_DIR/output.ulx"

# Copy final output
BUILD_OUTPUT="$BUILD_DIR/output.ulx"
if [ -f "$BUILD_OUTPUT" ]; then
  cp "$BUILD_OUTPUT" "$OUTPUT_FILE"
  SIZE=$(wc -c < "$OUTPUT_FILE" | tr -d ' ')
  echo "Compilation successful: $OUTPUT_FILE ($SIZE bytes)"
else
  echo "Error: Compiled output not found at $BUILD_OUTPUT"
  exit 1
fi
