# Kokopelli Reloaded

Kokopelli is a script-based CAD/CAM environment that uses Python as a hardware
description language. Designs are ordinary Python programs: geometry can be
parameterized, composed, rendered, and prepared for fabrication without leaving
the editor.

This fork is being revived after several years of inactivity. Version 0.3.0 now
runs on modern Python 3 and current macOS development tools.

## Current status

The following capabilities are verified in the current checkout:

- Python 3.12 runtime with declared support for Python 3.10 and newer;
- reproducible dependencies through `pyproject.toml` and `uv.lock`;
- native `libfab` compilation with current CMake and Apple Clang;
- the wxPython Phoenix editor and 2D canvas;
- all 15 bundled `.ko` examples, including interactive points and sliders;
- 16-bit heightmap PNG, multicolor PNG, and physically sized SVG export; and
- 21 automated tests covering the native geometry boundary, exports, and
  bundled examples.

The mandala, living-hinge, box, gear, and other examples now evaluate in Python
3. The complete evidence and staged roadmap are maintained in
[`REVIVAL.md`](REVIVAL.md).

3D rendering, STL/ASDF workflows, CAM machine output, cross-platform builds, and
standalone application packaging still require direct validation. Their presence
in the source tree should not yet be interpreted as a claim that they work.

## Quick start on macOS

Install the system prerequisites with Homebrew:

```bash
brew install cmake libpng uv
```

Clone the repository, create the isolated Python environment, and build the
native geometry library:

```bash
git clone https://github.com/TheBeachLab/kokopelli.git
cd kokopelli
make install
```

Start with a new design:

```bash
uv run kokopelli
```

Or open one of the bundled examples:

```bash
uv run kokopelli examples/mandala.ko
uv run kokopelli examples/gear.ko
```

The development launcher also supports module execution:

```bash
uv run python -m koko --help
```

## Verification

Run the native build and dependency check:

```bash
make check
```

Run the full automated suite:

```bash
make test
```

At the time of this README update, the integrated suite reports 21 passing
tests. Three export tests verify decoded image/vector content rather than merely
checking that files were created.

## Writing a design

A `.ko` file is a Python program that assigns one or more shapes to `cad`:

```python
from koko.lib.shapes import *

outer = circle(0, 0, 1)
inner = circle(0, 0, 0.45)

ring = outer - inner
ring.color = "red"

cad.shapes = [ring]
```

The bundled [`examples`](examples) directory contains 2D and 3D models,
parameterized designs, text, PCB layouts, and mechanical assemblies. Start with
`mandala.ko`, `gear.ko`, or `box.ko` to see the script-and-canvas workflow.

## Security warning

Kokopelli executes design files as Python. This is what makes designs flexible,
but it also means a `.ko` file can perform any action available to the current
user.

**Do not open an untrusted `.ko` file without inspecting it as source code
first.**

## History

Francisco Sanchez discovered Kokopelli while attending Fab Academy at Fab Lab
Barcelona in 2013. This fork began as an effort to preserve the directness of
script-based design: instead of manually pointing and clicking, a model can be
described, parameterized, repeated, and transformed as code.

The original Kokopelli was created by Matt Keeter at the MIT Center for Bits and
Atoms and grew out of the course “How to Make Something that Makes (Almost)
Anything.” It combines a Python design environment with the native `libfab`
geometry engine and a modular fabrication workflow.

This fork also contains PCB-library work derived from additions by Sam Calisch.
The PCB merge and the repository's unfinished dot-matrix-font and free-cutout
ideas remain roadmap items rather than completed features.

## Copyright

- © 2012–2013 Massachusetts Institute of Technology
- © 2013 Matt Keeter
- © 2017 Sam Calisch
- © 2018–2026 Francisco Sanchez

See [`LICENSE.md`](LICENSE.md) for the repository's license text.
