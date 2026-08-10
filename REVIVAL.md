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
- Automated smoke tests cover native-tree parsing, interval and vector division,
  current NumPy compatibility, runtime imports, and Python 3 syntax for examples.

## Not yet verified

These are capabilities present in the source, not claims that they work today:

- opening, editing, saving, and reloading every supported input type;
- PNG, SVG, STL, DOT, and ASDF export correctness;
- 3D OpenGL rendering and mesh operations;
- CAM workflows and output for each supported machine;
- Linux and Windows builds;
- standalone macOS application packaging and signing.

## Proposed stages

1. Add headless golden tests for 2D geometry and PNG/SVG export.
2. Exercise every bundled example in the GUI and repair evaluation failures.
3. Test 3D geometry, ASDF generation, STL round trips, and OpenGL rendering.
4. Validate CAM workflows one machine at a time using fixture inputs and expected
   output files, without connecting real equipment during automated tests.
5. Audit and finish the repository's explicit WIP areas: the dot-matrix font,
   the partial PCB-library merge, and free cutout shapes.
6. Package a self-contained macOS application, then add Linux support and CI.

Kokopelli executes design files as Python. Treat `.ko` files like source code and
only open files from trusted sources or inspect them first.
