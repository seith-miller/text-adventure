"""Station-map blip animation primitive (m13 #161).

The module under test is an ES module (game/station-map.mjs) — we
shell out to Node to run assertions against it. Node ≥18 ships with
Mir's End's CI and is required by the existing build/test pipeline.
"""

import json
import os
import shutil
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(ROOT, "game", "station-map.mjs")
DEMO_PATH = os.path.join(ROOT, "game", "mockups", "v6-map-blip.html")

# Must match game/ui.js KNOWN_ROOMS.
KNOWN_ROOMS = [
    "Crew Quarters",
    "Main Corridor",
    "Command Module",
    "Observation Cupola",
    "Life Support Module",
    "Hydroponics Lab",
    "Armament Bay",
    "Reactor Module",
    "Progress Ferry",
    "Soyuz Ferry",
    "Soyuz Reentry Capsule",
]

EXPECTED_WIDTH = 76
EXPECTED_HEIGHT = 19


def _node_available() -> bool:
    return shutil.which("node") is not None


def _run_node(script: str) -> dict:
    """Run a Node snippet that imports station-map.mjs and emits JSON
    on stdout. Returns the parsed object."""
    if not _node_available():
        pytest.skip("node not on PATH")
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    assert proc.returncode == 0, (
        f"node failed:\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )
    return json.loads(proc.stdout)


def test_module_file_exists():
    assert os.path.isfile(MODULE_PATH), f"missing {MODULE_PATH}"


def test_demo_page_exists():
    assert os.path.isfile(DEMO_PATH), f"missing {DEMO_PATH}"


def test_demo_page_imports_module():
    """The demo page must wire up to the actual module under test."""
    with open(DEMO_PATH, encoding="utf-8") as f:
        body = f.read()
    assert "../station-map.mjs" in body
    assert "renderMapFrame" in body
    assert "generateTransitionFrames" in body


def test_map_base_dimensions():
    result = _run_node(
        """
        import { MIR3_MAP_BASE, MAP_WIDTH, MAP_HEIGHT } from "./game/station-map.mjs";
        const rows = MIR3_MAP_BASE.split("\\n");
        process.stdout.write(JSON.stringify({
          width: MAP_WIDTH,
          height: MAP_HEIGHT,
          rowCount: rows.length,
          rowLengths: rows.map(r => [...r].length),
        }));
        """
    )
    assert result["width"] == EXPECTED_WIDTH
    assert result["height"] == EXPECTED_HEIGHT
    assert result["rowCount"] == EXPECTED_HEIGHT
    for i, length in enumerate(result["rowLengths"]):
        assert length == EXPECTED_WIDTH, (
            f"row {i} has {length} chars (expected {EXPECTED_WIDTH})"
        )


def test_all_known_rooms_have_anchors():
    """Every entry in game/ui.js KNOWN_ROOMS must have a coord."""
    result = _run_node(
        """
        import { ROOM_COORDS } from "./game/station-map.mjs";
        process.stdout.write(JSON.stringify({ keys: Object.keys(ROOM_COORDS) }));
        """
    )
    keys = set(result["keys"])
    for room in KNOWN_ROOMS:
        assert room in keys, f"ROOM_COORDS is missing {room!r}"


def test_anchors_are_inside_the_map():
    result = _run_node(
        """
        import { ROOM_COORDS, MAP_WIDTH, MAP_HEIGHT } from "./game/station-map.mjs";
        const out = {};
        for (const [name, c] of Object.entries(ROOM_COORDS)) out[name] = c;
        process.stdout.write(JSON.stringify(out));
        """
    )
    for name, coord in result.items():
        assert 0 <= coord["x"] < EXPECTED_WIDTH, f"{name} x out of bounds"
        assert 0 <= coord["y"] < EXPECTED_HEIGHT, f"{name} y out of bounds"


def test_anchors_land_on_visible_box_characters():
    """The anchor cell should sit on the room's label (a letter or an
    inside-box space), not on a corridor segment or border. Reads the
    char at each anchor and asserts it isn't a box-drawing glyph."""
    result = _run_node(
        """
        import { ROOM_COORDS, MIR3_MAP_BASE } from "./game/station-map.mjs";
        const rows = MIR3_MAP_BASE.split("\\n");
        const out = {};
        for (const [name, c] of Object.entries(ROOM_COORDS)) {
          out[name] = [...rows[c.y]][c.x];
        }
        process.stdout.write(JSON.stringify(out));
        """
    )
    box_glyphs = set("─│┌┐└┘┬┴├┤┼")
    for name, ch in result.items():
        assert ch not in box_glyphs, (
            f"{name} anchor sits on box-drawing glyph {ch!r}, not a label cell"
        )


def test_all_room_pairs_resolve_to_a_path():
    """Every ordered pair of distinct rooms must produce a non-empty
    corridor path — the demo cycles through all of them, and a null
    return would crash the visual confirmation flow."""
    result = _run_node(
        """
        import { ROOM_NAMES, debugPath } from "./game/station-map.mjs";
        const out = { failures: [], pairCount: 0 };
        for (const a of ROOM_NAMES) for (const b of ROOM_NAMES) {
          if (a === b) continue;
          out.pairCount++;
          const p = debugPath(a, b);
          if (!p || p.length < 1) out.failures.push(`${a} → ${b}`);
        }
        process.stdout.write(JSON.stringify(out));
        """
    )
    assert result["failures"] == [], f"unresolved pairs: {result['failures']}"
    assert result["pairCount"] >= 110  # 11 rooms × 10 others (Soyuz dup is OK)


def test_generate_transition_frames_shape():
    """generateTransitionFrames must return a string[] whose every
    entry matches MIR3_MAP_BASE in row count and visible character
    count. AsciiPlayer is permissive but our renderer guarantees this
    shape — verify it explicitly."""
    result = _run_node(
        """
        import {
          generateTransitionFrames,
          MAP_WIDTH,
          MAP_HEIGHT,
        } from "./game/station-map.mjs";
        const frames = generateTransitionFrames("Crew Quarters", "Command Module", 14);
        // Strip our inline tags to compare visible char counts.
        const stripTags = (s) => s.replace(/<\\/?(dim|bri)>/g, "");
        const rowDims = frames.map((f) => {
          const rows = stripTags(f).split("\\n");
          return { rowCount: rows.length, rowLens: rows.map(r => [...r].length) };
        });
        process.stdout.write(JSON.stringify({
          frameCount: frames.length,
          mapW: MAP_WIDTH,
          mapH: MAP_HEIGHT,
          rowDims,
          firstHasBri: frames[0].includes("<bri>"),
          firstHasDim: frames[0].includes("<dim>"),
        }));
        """
    )
    assert result["frameCount"] == 14
    for i, dims in enumerate(result["rowDims"]):
        assert dims["rowCount"] == result["mapH"], f"frame {i} row count"
        for j, length in enumerate(dims["rowLens"]):
            assert length == result["mapW"], (
                f"frame {i} row {j} has {length} chars (expected {result['mapW']})"
            )
    assert result["firstHasBri"], "blip should be wrapped in <bri> tags"
    assert result["firstHasDim"], "dimmed schematic should use <dim> tags"


def test_endpoint_frames_show_blip_at_anchor():
    """t=0 places the blip at the from-room anchor; t=1 places it at
    the to-room anchor. The bright cell in the rendered output should
    match ROOM_COORDS[from] / ROOM_COORDS[to]."""
    result = _run_node(
        """
        import {
          renderMapFrame,
          ROOM_COORDS,
        } from "./game/station-map.mjs";
        function blipCell(frame) {
          // Strip tags but track where <bri>█ sat in the source. The
          // emitted format is <dim>prefix</dim><bri>█</bri><dim>suffix</dim>
          // on a single row; locate that row, then find the visible
          // column of █ after stripping tags.
          const rows = frame.split("\\n");
          for (let y = 0; y < rows.length; y++) {
            const m = rows[y].match(/<bri>█<\\/bri>/);
            if (!m) continue;
            const before = rows[y].slice(0, m.index).replace(/<\\/?(dim|bri)>/g, "");
            return { x: [...before].length, y };
          }
          return null;
        }
        const fromCell = blipCell(renderMapFrame("Crew Quarters", "Command Module", 0));
        const toCell   = blipCell(renderMapFrame("Crew Quarters", "Command Module", 1));
        process.stdout.write(JSON.stringify({
          fromCell, toCell,
          fromAnchor: ROOM_COORDS["Crew Quarters"],
          toAnchor: ROOM_COORDS["Command Module"],
        }));
        """
    )
    assert result["fromCell"] == result["fromAnchor"]
    assert result["toCell"] == result["toAnchor"]


def test_non_adjacent_pair_routes_through_the_graph():
    """Crew Quarters → Progress Ferry must traverse the Reactor Module
    (Progress is only reachable from Reactor). The path should be
    longer than either edge alone."""
    result = _run_node(
        """
        import { debugPath } from "./game/station-map.mjs";
        const direct = debugPath("Crew Quarters", "Reactor Module");
        const chained = debugPath("Crew Quarters", "Progress Ferry");
        process.stdout.write(JSON.stringify({
          direct: direct.length,
          chained: chained.length,
          chainedTail: chained[chained.length - 1],
        }));
        """
    )
    assert result["chained"] > result["direct"]
    # Tail must be at Progress Ferry's anchor.
    assert result["chainedTail"] == {"x": 17, "y": 17}
