# Kokopelli revival

This document separates what the current revival has demonstrated from work that
still needs direct testing.

## Recovered baseline

- Python 3 port work from the repository's `python3` branch has been carried onto
  the current `master` history and corrected where automated conversion changed
  behavior.
- `libfab` configures and builds with current CMake and Apple Clang.
- Dependencies are declared in `pyproject.toml` and resolved reproducibly with
  `uv.lock`.
- The macOS application starts with wxPython Phoenix and renders both the
  default circle and the bundled multicolor involute-gear example in 2D.
- Every bundled `.ko` example executes under Python 3. The parameterized box,
  living-hinge, and mandala examples reconstruct their interactive primitives;
  all three also load in the macOS GUI, with the mandala and slider rendering.
- A fabrication-oriented 5×7 font now constructs European and Japanese labels
  from cutter-sized dots. Horizontal and vertical character spacing are
  independently controllable, with zero joining adjacent matrix cells. The same
  engine accepts arbitrary binary pixel-art patterns.
- Heightmap PNG, multicolor PNG, and physically sized SVG export run headlessly
  through the real export implementation and have deterministic content tests.
- Automated tests also cover native-tree parsing, interval and vector division,
  current NumPy compatibility, and runtime imports.

## Not yet verified

These are capabilities present in the source, not claims that they work today:

- opening, editing, saving, and reloading every supported input type;
- STL, DOT, and ASDF export correctness;
- the modal file-dialog portion of PNG and SVG export;
- 3D OpenGL rendering and mesh operations;
- CAM workflows and output for each supported machine;
- Linux and Windows builds;
- standalone macOS application packaging and signing.

## Proposed stages

1. Completed: add headless golden-style tests for 2D geometry and PNG/SVG
   export.
2. Completed: execute every bundled example and exercise the parameterized
   examples in the GUI.
3. Next: test 3D geometry, ASDF generation, STL round trips, and OpenGL
   rendering.
4. Validate CAM workflows one machine at a time using fixture inputs and expected
   output files, without connecting real equipment during automated tests.
5. Extend the dot-matrix work with calibrated V-bit variable-depth halftones,
   preserving both visible dot geometry and plunge-center/depth data for CAM.
6. Audit and finish the remaining explicit WIP areas: the partial PCB-library
   merge and free cutout shapes.
7. Package a self-contained macOS application, then add Linux support and CI.

Kokopelli executes design files as Python. Treat `.ko` files like source code and
only open files from trusted sources or inspect them first.
