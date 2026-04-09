"""Helper for driving glulxe (the Glulx interpreter) in headless tests.

The Homebrew build of glulxe links against glktermw, a curses-based GLK
implementation that requires a real TTY. This module spawns it inside a
pseudo-terminal via pty.fork, feeds it commands, captures the output, and
strips the ANSI/curses control codes so tests can make plain-text assertions.
"""

from __future__ import annotations

import os
import pty
import re
import select
import shutil
import time

# Match the various escape sequences glktermw emits
_ANSI_RE = re.compile(
    r"(?:\x1b\[[0-?]*[ -/]*[@-~])"   # CSI sequences
    r"|(?:\x1b[()*+][\x20-\x7e])"    # G0/G1 charset designators
    r"|(?:\x1b=)"                    # keypad mode
    r"|(?:\x1b>)"                    # numeric keypad mode
    r"|[\x0e\x0f\x07]"               # SO/SI/BEL
)


def have_glulxe() -> bool:
    """Return True if a glulxe binary is available on PATH."""
    return shutil.which("glulxe") is not None


def strip_ansi(s: str) -> str:
    """Remove ANSI/curses control sequences from terminal output."""
    return _ANSI_RE.sub("", s)


def normalize(s: str) -> str:
    """Strip ANSI codes and collapse whitespace for plain-text assertions."""
    cleaned = strip_ansi(s)
    # Collapse runs of whitespace (including the spaces glktermw uses for
    # cursor positioning) so multi-line assertions are easier
    return re.sub(r"\s+", " ", cleaned).strip()


def run_glulxe(
    story_path: str,
    inputs: list[str],
    timeout: float = 10.0,
) -> str:
    """Run glulxe against a story file, send the given inputs, and return
    the captured terminal output.

    Each input is a single command (no trailing newline). The function
    appends newlines and an extra "y\\n" at the end so the standard
    "Are you sure you want to quit?" prompt is satisfied.

    The returned string still contains ANSI codes; pass it through
    `strip_ansi()` or `normalize()` for assertions.
    """
    if not have_glulxe():
        raise RuntimeError("glulxe binary not found on PATH")
    if not os.path.isfile(story_path):
        raise FileNotFoundError(story_path)

    # Build the input stream. A leading newline absorbs any "press any key"
    # prompt that glktermw shows during the title screen — without it the
    # first character of the first command gets eaten. The final "y\n"
    # handles the standard quit confirmation.
    payload = ("\n" + "\n".join(inputs) + "\ny\n").encode("utf-8")

    pid, fd = pty.fork()
    if pid == 0:
        # Child: exec glulxe with a sane TERM
        os.environ["TERM"] = "xterm"
        try:
            os.execvp("glulxe", ["glulxe", story_path])
        except Exception:
            os._exit(127)

    # Parent: write the input, then read until the child exits or we time out
    try:
        os.write(fd, payload)
    except OSError:
        pass

    output = bytearray()
    deadline = time.time() + timeout
    while time.time() < deadline:
        rl, _, _ = select.select([fd], [], [], 0.25)
        if rl:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            output.extend(chunk)
        else:
            try:
                pid_wait, _ = os.waitpid(pid, os.WNOHANG)
                if pid_wait != 0:
                    # Drain any remaining output
                    try:
                        while True:
                            chunk = os.read(fd, 4096)
                            if not chunk:
                                break
                            output.extend(chunk)
                    except OSError:
                        pass
                    break
            except ChildProcessError:
                break

    # Make sure the child is gone
    try:
        os.kill(pid, 9)
    except ProcessLookupError:
        pass
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass
    try:
        os.close(fd)
    except OSError:
        pass

    return output.decode("utf-8", errors="replace")
