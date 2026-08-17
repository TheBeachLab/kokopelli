from pathlib import Path
import subprocess
import sys

from PIL import Image
import pytest

import koko
import koko.prims.points
import koko.prims.utils
from koko.cli import _project_root, runtime_check
from koko.fab.fabvars import FabVars
from koko.prims.core import PrimSet


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_dependencies_and_native_library():
    assert runtime_check() == 0


def test_frozen_project_root_uses_bundle_resources(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert _project_root() == tmp_path


def test_example_designs_are_valid_python3():
    examples = sorted((ROOT / "examples").glob("*.ko"))
    assert examples

    for example in examples:
        compile(example.read_text(), str(example), "exec")


@pytest.mark.parametrize("example", sorted((ROOT / "examples").glob("*.ko")))
def test_examples_execute(example):
    source = example.read_text()
    namespace = {}
    interactive = source.startswith("##    Geometry header    ##")

    if interactive:
        lines = source.splitlines()
        koko.PRIMS = PrimSet()
        reconstruction = eval(lines[1], {"koko": koko})
        koko.PRIMS.reconstruct(reconstruction)
        namespace.update(koko.PRIMS.dict)
        source = "\n".join(lines[3:])

    namespace["cad"] = FabVars()
    exec(compile(source, str(example), "exec"), namespace)

    assert namespace["cad"].shapes
    if interactive:
        assert all(primitive.valid for primitive in koko.PRIMS.shapes)


def test_development_launcher_help():
    result = subprocess.run(
        [sys.executable, str(ROOT / "kokopelli"), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Script-based CAD/CAM" in result.stdout


def test_notarization_tool_help():
    result = subprocess.run(
        [sys.executable, str(ROOT / "util" / "app" / "notarize_app.py"), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Developer ID-signed macOS application" in result.stdout
    assert "--verify-only" in result.stdout


def test_dmg_tool_help():
    result = subprocess.run(
        [sys.executable, str(ROOT / "util" / "app" / "make_dmg.py"), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "drag-to-Applications DMG" in result.stdout
    assert "--profile" in result.stdout


def test_dmg_background_contains_install_arrow(tmp_path):
    from util.app.make_dmg import BACKGROUND_SIZE, create_background

    background = tmp_path / "background.png"
    create_background(background, "Kokopelli")

    with Image.open(background) as image:
        assert image.size == BACKGROUND_SIZE
        assert image.getpixel((330, 215)) == (38, 118, 255)
        assert image.getpixel((440, 215)) == (38, 118, 255)
