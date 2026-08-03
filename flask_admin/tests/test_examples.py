"""
Test suite for flask-admin examples.

This test suite validates that each example in the examples directory
can be started successfully and that the /admin endpoint returns HTTP 200.

Each example is run using the env in examples/<example>/pyproject.toml.
"""

import subprocess
import time
from pathlib import Path

import pytest
import requests  # type: ignore

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"


def get_example_directories() -> list[tuple[str, Path]]:
    """
    Get all subdirectories in the examples directory that contain a main.py file.

    Returns:
        List of tuples (example_name, example_path)
    """
    if not EXAMPLES_DIR.exists():
        return []

    examples = []
    for item in EXAMPLES_DIR.iterdir():
        if item.is_dir():
            main_py = item / "main.py"
            if main_py.exists():
                examples.append((item.name, item))

    return sorted(examples)


@pytest.mark.parametrize("example_name,example_path", get_example_directories())
def test_example_runs(example_name: str, example_path: Path):
    """
    Test that the example can be started and that the /admin endpoint returns HTTP 200.

    Args:
        example_name: Name of the example.
        example_path: Path to the example directory.
    """
    process = subprocess.Popen(
        [
            "uv",
            "run",
            "-q",
            "main.py",
        ],  # -q filters out uv warnings about different venv for the example
        cwd=example_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for the server to start
        time.sleep(5)

        # Check if the /admin endpoint is reachable
        response = requests.get("http://localhost:5000/admin")
        assert (
            response.status_code == 200
        ), f"/admin endpoint returned {response.status_code}"
    finally:
        process.terminate()
        process.wait()
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise AssertionError(
                f"Example '{example_name}' failed to run."
                # f"STDOUT: {stdout.decode()}"
                f"STDERR: {stderr.decode()}"
            )
        else:
            print(f"Example '{example_name}' ran successfully.")
