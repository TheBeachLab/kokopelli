#!/usr/bin/env python3
"""Build a self-contained Kokopelli application bundle for macOS."""

from __future__ import annotations

from pathlib import Path
import platform
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "dist" / "Kokopelli.app"
ICON = ROOT / "util" / "app" / "ko.icns"
SPEC = ROOT / "util" / "app" / "Kokopelli.spec"


def run(*command: str | Path) -> None:
    printable = " ".join(str(part) for part in command)
    print(f"+ {printable}", flush=True)
    subprocess.run([str(part) for part in command], cwd=ROOT, check=True)


def main() -> int:
    if platform.system() != "Darwin":
        raise SystemExit("Kokopelli.app must be built on macOS")

    if not (ROOT / "libfab" / "libfab.dylib").is_file():
        raise SystemExit("libfab.dylib is missing; run `make build` first")

    icon_source = Path(__file__).with_name("make_icon.py")
    if not ICON.is_file() or ICON.stat().st_mtime < icon_source.stat().st_mtime:
        run(sys.executable, icon_source, ICON)

    run(
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        ROOT / "dist",
        "--workpath",
        ROOT / "build" / "pyinstaller",
        SPEC,
    )
    run(sys.executable, ROOT / "util" / "app" / "check_app.py", APP_DIR)

    print(f"\nBuilt {APP_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
