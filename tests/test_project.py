from pathlib import Path
import subprocess
import sys

import pytest

from koko.cli import runtime_check
from koko.fab.fabvars import FabVars


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_dependencies_and_native_library():
    assert runtime_check() == 0


def test_example_designs_are_valid_python3():
    examples = sorted((ROOT / "examples").glob("*.ko"))
    assert examples

    for example in examples:
        compile(example.read_text(), str(example), "exec")


@pytest.mark.parametrize("example", sorted((ROOT / "examples").glob("*.ko")))
def test_noninteractive_examples_execute(example):
    source = example.read_text()
    if source.startswith("##    Geometry header    ##"):
        pytest.skip("interactive example requires GUI primitives")

    namespace = {"cad": FabVars()}
    exec(compile(source, str(example), "exec"), namespace)

    assert namespace["cad"].shapes


def test_development_launcher_help():
    result = subprocess.run(
        [sys.executable, str(ROOT / "kokopelli"), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Script-based CAD/CAM" in result.stdout
