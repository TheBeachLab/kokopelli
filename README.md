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
- a self-contained Apple Silicon `Kokopelli.app` bundle for macOS;
- Developer ID signing, Apple notarization, ticket stapling, and Gatekeeper
  validation for public macOS distribution;
- all 16 bundled `.ko` examples, including interactive points and sliders;
- tool-aware 5×7 labels and arbitrary binary pixel art;
- 16-bit heightmap PNG, multicolor PNG, and physically sized SVG export; and
- automated tests covering the native geometry boundary, exports, and
  bundled examples.

The mandala, living-hinge, box, gear, dot-matrix label, and other examples now
evaluate in Python 3. The complete evidence and staged roadmap are maintained in
[`REVIVAL.md`](REVIVAL.md).

3D rendering, STL/ASDF workflows, CAM machine output, and cross-platform builds
still require direct validation. Their presence in the source tree should not
yet be interpreted as a claim that they work.

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

## Build the macOS application

Create a self-contained application that can be opened from Finder without a
separate Python installation:

```bash
make app
open dist/Kokopelli.app
```

The build includes Python, wxPython, OpenGL support, the native `libfab`
library, examples, documentation, and the editable Kokopelli library sources.
It also registers `.ko` as a Kokopelli design format and applies a local ad hoc
code signature. Run its structural, signature, architecture, and bundled
runtime checks again with:

```bash
make app-check
```

[PyInstaller builds for the selected macOS target architecture](https://pyinstaller.org/en/stable/usage.html#cmdoption-target-architecture).
The current bundle and distributable ZIP have been verified on Apple Silicon
(`arm64`). Release builds use an
[Apple Developer ID certificate](https://developer.apple.com/help/account/certificates/create-developer-id-certificates)
and [notarization](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution),
while local builds intentionally require neither credential.

For public distribution, first store reusable notary credentials in the local
macOS Keychain. The profile can be used by multiple app build workflows for the
same Apple developer account and team:

```bash
xcrun notarytool store-credentials PROFILE_NAME \
  --apple-id YOUR_APPLE_ID \
  --team-id YOUR_TEAM_ID
```

Then build Kokopelli with any `Developer ID Application` identity and pass the
generic Keychain profile to the reusable notarization tool:

```bash
make app-notarize \
  DEVELOPER_IDENTITY="Developer ID Application: Your Name (TEAM_ID)" \
  NOTARY_PROFILE="PROFILE_NAME"
```

`util/app/notarize_app.py` is not Kokopelli-specific: it accepts any correctly
signed `.app`, verifies Developer ID and Hardened Runtime, submits it to Apple,
staples and validates the ticket, checks Gatekeeper acceptance, and creates the
final ZIP archive. The complete Kokopelli workflow has been exercised through
an accepted Apple notarization submission and validation of the app after
extracting the resulting ZIP.

## Verification

Run the native build and dependency check:

```bash
make check
```

Run the full automated suite:

```bash
make test
```

At the time of this README update, the integrated suite reports 39 passing
tests. Three export tests verify decoded image/vector content rather than merely
checking that files were created; fifteen tests exercise glyph coverage,
physical spacing, Unicode expansion, pixel art, and MathTree generation. The
release-tooling checks also exercise the application and notarization command
line interfaces.

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

## Tool-aware dot-matrix labels

`koko.lib.dottext` constructs labels from physical dots rather than external
font outlines. The dot diameter can match a milling cutter, while dot clearance
and character spacing remain independent:

```python
from koko.lib.dottext import text

label = text(
    "KOKOPELLI\nÄÖÜ · ココペリ",
    dot_diameter=0.8,
    dot_spacing=0.25,
    horizontal_spacing=1,
    vertical_spacing=1,
)

cad.mm_per_unit = 1
cad.shapes = [label]
```

Horizontal and vertical character spacing count empty matrix columns and rows.
Their conventional default is one; setting either value to zero places 5×7
cells directly beside one another, allowing continuous double-width or
double-height patterns.

The map covers the printable IBM-850 multilingual Latin-1 repertoire, common
European Latin Extended-A letters, JIS X 0201 half-width katakana, full-width
katakana input, and a compact hiragana set. A 5×7 cell is not sufficient for
general kanji. IBM identifies CP850 as
its Latin-1 multinational PC page and JIS X 0201 separately as Japanese CCSID
897 ([IBM encoding table](https://www.ibm.com/docs/en/i/7.5.0?topic=encodings-fileencoding-values-i-ccsid)).
The historical ASCII/katakana forms follow the public-domain
[HD44780A00 character table](https://commons.wikimedia.org/wiki/File:Charset.gif).

Arbitrary binary matrices use the same physical controls:

```python
from koko.lib.dottext import pattern

art = pattern(
    (
        "00100",
        "01110",
        "11111",
        "01010",
    ),
    dot_diameter=1.0,
    dot_spacing=0.3,
)
```

Open `examples/dottext.ko` to adjust cutter diameter, dot clearance, horizontal
spacing, and vertical spacing with interactive sliders.

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
The first fabrication-oriented dot-matrix font stage is now implemented. The
PCB merge, V-bit variable-depth halftones, and free-cutout ideas remain roadmap
items rather than completed features.

## Copyright

- © 2012–2013 Massachusetts Institute of Technology
- © 2013 Matt Keeter
- © 2017 Sam Calisch
- © 2018–2026 Francisco Sanchez

See [`LICENSE.md`](LICENSE.md) for the repository's license text.
Third-party attributions for adapted glyph data are preserved in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
