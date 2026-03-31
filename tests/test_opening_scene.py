"""Tests for the opening scene (game/story/opening.ink)."""

import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPENING_INK = os.path.join(ROOT, "game", "story", "opening.ink")
OPENING_JSON = os.path.join(ROOT, "game", "dist", "story", "opening.json")


def _ensure_compiled():
    """Build the story if the compiled JSON doesn't exist."""
    if not os.path.isfile(OPENING_JSON):
        subprocess.run(["npm", "run", "build:story"], cwd=ROOT, timeout=60, check=True)


def _run_inkjs(script: str) -> subprocess.CompletedProcess:
    """Run a Node.js script that uses inkjs and return the result."""
    return subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_opening_ink_exists():
    """opening.ink file exists in game/story/."""
    assert os.path.isfile(OPENING_INK), "game/story/opening.ink not found"


def test_opening_compiles():
    """opening.ink compiles via npm run build:story without errors."""
    result = subprocess.run(
        ["npm", "run", "build:story"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, f"Compilation failed: {result.stderr}"
    assert os.path.isfile(OPENING_JSON), "Compiled opening.json not found"


def test_compiled_json_is_valid():
    """Compiled JSON is valid and contains inkVersion."""
    _ensure_compiled()
    with open(OPENING_JSON) as f:
        data = json.load(f)
    assert "inkVersion" in data, "Not a valid ink story JSON"


def test_compiled_json_loadable_by_inkjs():
    """Compiled JSON loads in inkjs without errors."""
    _ensure_compiled()
    result = _run_inkjs(
        f"""
        const {{Story}} = require('inkjs');
        const fs = require('fs');
        const json = fs.readFileSync('{OPENING_JSON}', 'utf-8');
        const story = new Story(json);
        console.log('OK');
        """
    )
    assert result.returncode == 0, f"inkjs load failed: {result.stderr}"
    assert "OK" in result.stdout


def test_global_variables_exist():
    """Story declares oxygen, morale, and has_flashlight variables."""
    _ensure_compiled()
    result = _run_inkjs(
        f"""
        const {{Story}} = require('inkjs');
        const fs = require('fs');
        const story = new Story(fs.readFileSync('{OPENING_JSON}', 'utf-8'));
        const vars = ['oxygen', 'morale', 'has_flashlight'];
        for (const v of vars) {{
            const val = story.variablesState[v];
            if (val === undefined || val === null) {{
                console.error('Missing variable: ' + v);
                process.exit(1);
            }}
            console.log(v + '=' + val);
        }}
        console.log('OK');
        """
    )
    assert result.returncode == 0, f"Variable check failed: {result.stderr}"
    assert "OK" in result.stdout
    assert "oxygen=100" in result.stdout
    assert "morale=50" in result.stdout


def test_no_dead_ends_path_search():
    """All three opening choices lead to a complete playthrough (no dead ends)."""
    _ensure_compiled()
    # Test first choice for each of the three opening paths
    for first_choice in [0, 1, 2]:
        result = _run_inkjs(
            f"""
            const {{Story}} = require('inkjs');
            const fs = require('fs');
            const story = new Story(fs.readFileSync('{OPENING_JSON}', 'utf-8'));
            let steps = 0;
            let firstChoice = true;
            while (story.canContinue || story.currentChoices.length > 0) {{
                if (story.canContinue) story.Continue();
                if (story.currentChoices.length > 0) {{
                    if (firstChoice) {{
                        story.ChooseChoiceIndex({first_choice});
                        firstChoice = false;
                    }} else {{
                        story.ChooseChoiceIndex(0);
                    }}
                    steps++;
                }}
                if (steps > 100) {{ console.error('LOOP'); process.exit(1); }}
            }}
            console.log('OK:' + steps);
            """
        )
        assert result.returncode == 0, (
            f"Path starting with choice {first_choice} failed: {result.stderr}"
        )
        assert "OK:" in result.stdout


def test_ascii_tags_emitted():
    """ASCII art tags are emitted at scene transitions."""
    _ensure_compiled()
    result = _run_inkjs(
        f"""
        const {{Story}} = require('inkjs');
        const fs = require('fs');
        const story = new Story(fs.readFileSync('{OPENING_JSON}', 'utf-8'));
        const tags = new Set();
        let steps = 0;
        while (story.canContinue || story.currentChoices.length > 0) {{
            if (story.canContinue) {{
                story.Continue();
                for (const t of story.currentTags) {{
                    if (t.startsWith('ascii:')) tags.add(t.trim());
                }}
            }}
            if (story.currentChoices.length > 0) {{
                story.ChooseChoiceIndex(0);
                steps++;
            }}
            if (steps > 100) {{ process.exit(1); }}
        }}
        console.log(JSON.stringify([...tags]));
        """
    )
    assert result.returncode == 0, f"Tag collection failed: {result.stderr}"
    collected = json.loads(result.stdout.strip())
    expected = ["ascii: darkness", "ascii: bunks", "ascii: corridor",
                "ascii: command_module", "ascii: radio", "ascii: earth_from_orbit",
                "ascii: earth_burning"]
    for tag in expected:
        assert tag in collected, f"Missing tag: {tag}"


def test_oxygen_decreases():
    """Oxygen decreases over the course of the story."""
    _ensure_compiled()
    result = _run_inkjs(
        f"""
        const {{Story}} = require('inkjs');
        const fs = require('fs');
        const story = new Story(fs.readFileSync('{OPENING_JSON}', 'utf-8'));
        let steps = 0;
        while (story.canContinue || story.currentChoices.length > 0) {{
            if (story.canContinue) story.Continue();
            if (story.currentChoices.length > 0) {{
                story.ChooseChoiceIndex(0);
                steps++;
            }}
            if (steps > 100) process.exit(1);
        }}
        const oxygen = story.variablesState['oxygen'];
        console.log('oxygen=' + oxygen);
        if (oxygen >= 100) process.exit(1);
        if (oxygen <= 0) process.exit(1);
        console.log('OK');
        """
    )
    assert result.returncode == 0, f"Oxygen check failed: {result.stderr}"
    assert "OK" in result.stdout


def test_flashlight_acquired():
    """Player acquires the flashlight during the story."""
    _ensure_compiled()
    result = _run_inkjs(
        f"""
        const {{Story}} = require('inkjs');
        const fs = require('fs');
        const story = new Story(fs.readFileSync('{OPENING_JSON}', 'utf-8'));
        let steps = 0;
        while (story.canContinue || story.currentChoices.length > 0) {{
            if (story.canContinue) story.Continue();
            if (story.currentChoices.length > 0) {{
                story.ChooseChoiceIndex(0);
                steps++;
            }}
            if (steps > 100) process.exit(1);
        }}
        const fl = story.variablesState['has_flashlight'];
        if (!fl) process.exit(1);
        console.log('OK');
        """
    )
    assert result.returncode == 0, f"Flashlight check failed: {result.stderr}"
    assert "OK" in result.stdout


def test_branching_paths_exist():
    """Different opening choices produce different story text."""
    _ensure_compiled()
    texts = []
    for choice in [0, 1, 2]:
        result = _run_inkjs(
            f"""
            const {{Story}} = require('inkjs');
            const fs = require('fs');
            const story = new Story(fs.readFileSync('{OPENING_JSON}', 'utf-8'));
            let text = '';
            let first = true;
            let steps = 0;
            while (story.canContinue || story.currentChoices.length > 0) {{
                if (story.canContinue) text += story.Continue();
                if (story.currentChoices.length > 0) {{
                    story.ChooseChoiceIndex(first ? {choice} : 0);
                    first = false;
                    steps++;
                }}
                if (steps > 100) process.exit(1);
            }}
            console.log(text.substring(0, 500));
            """
        )
        assert result.returncode == 0
        texts.append(result.stdout)
    # All three paths should produce different text
    assert texts[0] != texts[1], "Path 0 and 1 should differ"
    assert texts[0] != texts[2], "Path 0 and 2 should differ"
    assert texts[1] != texts[2], "Path 1 and 2 should differ"


def test_scene_ends_at_clear_boundary():
    """Story ends (reaches -> END) on all paths."""
    _ensure_compiled()
    for choice in [0, 1, 2]:
        result = _run_inkjs(
            f"""
            const {{Story}} = require('inkjs');
            const fs = require('fs');
            const story = new Story(fs.readFileSync('{OPENING_JSON}', 'utf-8'));
            let steps = 0;
            let first = true;
            while (story.canContinue || story.currentChoices.length > 0) {{
                if (story.canContinue) story.Continue();
                if (story.currentChoices.length > 0) {{
                    story.ChooseChoiceIndex(first ? {choice} : 0);
                    first = false;
                    steps++;
                }}
                if (steps > 100) {{ console.error('LOOP'); process.exit(1); }}
            }}
            // If we get here, story ended normally (-> END)
            if (story.currentChoices.length > 0) process.exit(1);
            console.log('OK');
            """
        )
        assert result.returncode == 0, f"Path {choice} did not end cleanly"
        assert "OK" in result.stdout
