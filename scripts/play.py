#!/usr/bin/env python3
"""
Headless play harness for MIR'S END. Wraps the glulxe interpreter so a
caller (a human, a script, or Claude) can drive a full playthrough from
the command line and get back a transcript.

## Usage

Commands on stdin, one per line. Transcript and final state as JSON on
stdout.

```
echo 'open locker
take flashlight
switch on flashlight
pull lever
n' | scripts/play.py
```

Or pass commands as JSON on stdin with --json:

```
echo '["open locker","take flashlight"]' | scripts/play.py --json
```

Options:
  --story PATH   path to the compiled .ulx story (default: game/dist/story.ulx)
  --timeout N    seconds to wait for interpreter output (default: 25)
  --raw          print the raw, un-normalized output (keeps ANSI codes)
  --json         read commands as a JSON array on stdin
  --pretty       indent the JSON output

## Return format

```json
{
  "story": "game/dist/story.ulx",
  "commands": ["open locker", "..."],
  "transcript": "<normalized terminal output>",
  "turns": N
}
```

## Limitations

This wrapper sends the whole command list to glulxe at once, then reads
its output until the interpreter exits. glulxe on PATH links against
glktermw, which pages long responses and consumes keystrokes at the
MORE prompt. In practice that means sequences of ~10 commands or less
return clean transcripts; longer sequences get truncated as the pager
eats queued input.

For a full canonical-arc playthrough (~20 commands) use the Playwright
harness in tests/e2e/canonical-arc.spec.ts. The proper fix (interactive
per-turn I/O against a Glk backend without paging) is tracked in the
MCP-server issue.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

# Reuse the driver the integration tests already ship.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tests"))
from glulxe_driver import have_glulxe, normalize, run_glulxe, strip_ansi  # noqa: E402


DEFAULT_STORY = "game/dist/story.ulx"


def read_commands(stream, as_json: bool) -> list[str]:
    raw = stream.read()
    if as_json:
        parsed = json.loads(raw)
        if not isinstance(parsed, list) or not all(isinstance(c, str) for c in parsed):
            raise ValueError("--json expects an array of strings on stdin")
        return [c.strip() for c in parsed if c.strip()]
    return [line.strip() for line in raw.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless MIR'S END play harness.")
    parser.add_argument("--story", default=DEFAULT_STORY, help="path to the compiled .ulx")
    parser.add_argument("--timeout", type=float, default=25.0, help="interpreter wait in seconds")
    parser.add_argument("--raw", action="store_true", help="emit raw un-normalized output")
    parser.add_argument("--json", action="store_true", help="read commands as a JSON array")
    parser.add_argument("--pretty", action="store_true", help="indent the JSON output")
    args = parser.parse_args()

    if not have_glulxe():
        sys.stderr.write("glulxe binary not found on PATH. Install a Glulx interpreter.\n")
        return 127

    story = pathlib.Path(args.story)
    if not story.is_file():
        sys.stderr.write(f"story file not found: {story}\n")
        return 2

    commands = read_commands(sys.stdin, as_json=args.json)
    raw_output = run_glulxe(str(story), commands, timeout=args.timeout)
    transcript = strip_ansi(raw_output) if args.raw else normalize(raw_output)

    result = {
        "story": str(story),
        "commands": commands,
        "transcript": transcript,
        "turns": len(commands),
    }

    indent = 2 if args.pretty else None
    sys.stdout.write(json.dumps(result, indent=indent, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
