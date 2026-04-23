"""
Golden-file voice translation test for renderShipStateForArgon().

Catches voice regressions separately from structural regressions.
The golden file lives at tests/golden/ship-state-voice-default.txt.
"""

import json
import os
import subprocess
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN_DIR = os.path.join(REPO_ROOT, "tests", "golden")
GOLDEN_FILE = os.path.join(GOLDEN_DIR, "ship-state-voice-default.txt")

IMPORT_LINE = 'import { initShipState, renderShipStateForArgon } from "./lib/ship-state.js";'


def run_js(script):
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"JS error:\n{result.stderr}")
    return result.stdout.strip()


class TestVoiceGoldenFile:
    def test_default_state_matches_golden(self):
        """Default ship-state voice output must match the golden file exactly."""
        actual = run_js(f"""
            {IMPORT_LINE}
            initShipState();
            console.log(renderShipStateForArgon());
        """)
        with open(GOLDEN_FILE, "r") as f:
            expected = f.read().strip()
        assert actual == expected, (
            f"Voice output does not match golden file.\n"
            f"To update, run:\n"
            f"  node --input-type=module -e '{IMPORT_LINE} initShipState(); "
            f"console.log(renderShipStateForArgon());' > {GOLDEN_FILE}\n"
        )

    def test_no_em_dashes_in_golden(self):
        """The golden file itself must not contain em-dashes."""
        with open(GOLDEN_FILE, "r") as f:
            content = f.read()
        assert "\u2014" not in content, "Golden file contains em-dash"
        assert "\u2013" not in content, "Golden file contains en-dash"

    def test_no_assistant_tone(self):
        """Voice output should avoid assistant-like phrases."""
        actual = run_js(f"""
            {IMPORT_LINE}
            initShipState();
            console.log(renderShipStateForArgon());
        """)
        forbidden = [
            "I would",
            "I think",
            "I believe",
            "Let me",
            "Sure,",
            "Of course",
            "I can",
            "I'll",
            "Happy to",
        ]
        for phrase in forbidden:
            assert phrase not in actual, f"Found assistant tone phrase: '{phrase}'"

    def test_voice_compliance_after_events(self):
        """Voice output remains compliant after applying multiple deltas."""
        actual = run_js(f"""
            import {{ initShipState, tickShipState, applyDelta, renderShipStateForArgon }} from "./lib/ship-state.js";
            initShipState();
            applyDelta("power-is-restored", {{}});
            applyDelta("cannon_fired", {{}});
            for (let i = 0; i < 6; i++) tickShipState();
            console.log(renderShipStateForArgon());
        """)
        # No em-dashes
        assert "\u2014" not in actual
        assert "\u2013" not in actual
        # Still has structure
        assert "[Time onboard]" in actual
        assert "[Where we are]" in actual
        assert "[My systems]" in actual
