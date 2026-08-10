from collections import Counter
from pathlib import Path
from types import SimpleNamespace
import threading
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image as PILImage

from koko.export import ExportTaskCad
from koko.fab.fabvars import FabVars
from koko.lib.shapes2d import circle, rectangle


def export_task(filename: Path, cad: FabVars, **settings) -> ExportTaskCad:
    """Build a synchronous export task without constructing a GUI window."""
    task = object.__new__(ExportTaskCad)
    task.filename = str(filename)
    task.extension = filename.suffix.removeprefix(".")
    task.cad = cad
    task.resolution = settings.get("resolution", 12)
    task.make_heightmap = settings.get("make_heightmap", True)
    task.event = threading.Event()
    task.c_event = threading.Event()
    task.window = SimpleNamespace(progress=0)
    return task


def circle_cad() -> FabVars:
    cad = FabVars()
    cad.mm_per_unit = 1
    cad.border = 0.05
    shape = circle(0, 0, 1)
    shape.color = (255, 0, 0)
    cad.shapes = [shape]
    return cad


def test_heightmap_png_export(tmp_path):
    target = tmp_path / "circle.png"
    export_task(target, circle_cad()).export_png()

    with PILImage.open(target) as image:
        pixels = np.array(image)
        assert image.format == "PNG"
        assert image.mode == "I;16"
        assert image.size == (25, 25)

    assert Counter(pixels.flatten()) == Counter({65535: 448, 0: 177})


def test_color_png_export(tmp_path):
    cad = FabVars()
    cad.mm_per_unit = 1
    cad.border = 0.05
    red = circle(-0.4, 0, 0.6)
    red.color = (255, 0, 0)
    blue = rectangle(0, 0.8, -0.5, 0.5)
    blue.color = (0, 0, 255)
    cad.shapes = [red, blue]

    target = tmp_path / "colors.png"
    export_task(
        target, cad, resolution=16, make_heightmap=False
    ).export_png()

    with PILImage.open(target) as image:
        pixels = np.array(image)
        assert image.mode == "RGB"
        assert image.size == (30, 20)

    colors, counts = np.unique(
        pixels.reshape(-1, 3), axis=0, return_counts=True
    )
    assert {
        tuple(color): int(count) for color, count in zip(colors, counts)
    } == {
        (0, 0, 0): 151,
        (0, 0, 255): 164,
        (255, 0, 0): 285,
    }


def test_svg_export_has_physical_size_color_and_closed_contour(tmp_path):
    target = tmp_path / "circle.svg"
    export_task(target, circle_cad()).export_svg()

    root = ET.parse(target).getroot()
    paths = list(root)

    assert root.attrib == {
        "version": "1.1",
        "width": "2.1mm",
        "height": "2.1mm",
        "viewBox": "0 0 7.44094 7.44094",
    }
    assert len(paths) == 1
    assert "stroke:rgb(255,0,0)" in paths[0].attrib["style"]
    assert paths[0].attrib["d"].startswith("M")
    assert paths[0].attrib["d"].endswith(" Z")
    assert paths[0].attrib["d"].count("L") == 91
