"""Tests for the GitHub Actions CI workflow configuration."""

import os
import yaml
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW_PATH = os.path.join(ROOT, ".github", "workflows", "ci.yml")


@pytest.fixture
def workflow():
    with open(WORKFLOW_PATH) as f:
        return yaml.safe_load(f)


def test_ci_workflow_exists():
    assert os.path.isfile(WORKFLOW_PATH), "CI workflow file not found"


def test_triggers_on_push_to_main(workflow):
    # YAML parses 'on' as boolean True
    triggers = workflow[True]
    assert "push" in triggers
    assert "main" in triggers["push"]["branches"]


def test_triggers_on_pull_request_to_main(workflow):
    triggers = workflow[True]
    assert "pull_request" in triggers
    assert "main" in triggers["pull_request"]["branches"]


def test_uses_node_22(workflow):
    steps = workflow["jobs"]["build-and-test"]["steps"]
    node_step = next(s for s in steps if s.get("uses", "").startswith("actions/setup-node"))
    assert node_step["with"]["node-version"] == "22"


def test_uses_python_312(workflow):
    steps = workflow["jobs"]["build-and-test"]["steps"]
    python_step = next(s for s in steps if s.get("uses", "").startswith("actions/setup-python"))
    assert python_step["with"]["python-version"] == "3.12"


def test_runs_biome_check(workflow):
    steps = workflow["jobs"]["build-and-test"]["steps"]
    run_commands = [s.get("run", "") for s in steps]
    assert any("biome check" in cmd for cmd in run_commands)


def test_runs_typescript_build(workflow):
    steps = workflow["jobs"]["build-and-test"]["steps"]
    run_commands = [s.get("run", "") for s in steps]
    assert any("build:ts" in cmd for cmd in run_commands)


def test_runs_pytest(workflow):
    steps = workflow["jobs"]["build-and-test"]["steps"]
    run_commands = [s.get("run", "") for s in steps]
    assert any("pytest" in cmd for cmd in run_commands)


def test_runs_npm_test(workflow):
    steps = workflow["jobs"]["build-and-test"]["steps"]
    run_commands = [s.get("run", "") for s in steps]
    assert any("npm test" in cmd for cmd in run_commands)


def test_does_not_compile_inform7(workflow):
    """CI must not try to compile Inform 7 source."""
    steps = workflow["jobs"]["build-and-test"]["steps"]
    run_commands = [s.get("run", "") for s in steps]
    all_commands = " ".join(run_commands)
    assert "build:story" not in all_commands
    assert "compile-inform7" not in all_commands


def test_uses_caching(workflow):
    steps = workflow["jobs"]["build-and-test"]["steps"]
    node_step = next(s for s in steps if s.get("uses", "").startswith("actions/setup-node"))
    python_step = next(s for s in steps if s.get("uses", "").startswith("actions/setup-python"))
    assert node_step["with"].get("cache") == "npm"
    assert python_step["with"].get("cache") == "pip"
