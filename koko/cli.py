"""Command-line entry point for kokopelli."""

from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
import sys

import koko


def _project_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kokopelli",
        description="Script-based CAD/CAM using Python as a design language.",
    )
    parser.add_argument("filename", nargs="?", help="design or model to open")
    parser.add_argument("--version", action="version", version=f"%(prog)s {koko.VERSION}")
    parser.add_argument(
        "--check",
        action="store_true",
        help="check runtime dependencies and the native geometry library, then exit",
    )
    return parser


def runtime_check() -> int:
    failures: list[str] = []
    for module_name in ("wx", "numpy", "OpenGL", "PIL"):
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover - exact import failures are platform-specific
            failures.append(f"{module_name}: {type(exc).__name__}: {exc}")

    try:
        importlib.import_module("koko.c.libfab")
    except Exception as exc:
        failures.append(f"libfab: {type(exc).__name__}: {exc}")

    if failures:
        print("kokopelli runtime check failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"kokopelli {koko.VERSION}: runtime check passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    root = _project_root()
    koko.BASE_DIR = os.fspath(root) + os.sep
    koko.BUNDLED = bool(getattr(sys, "frozen", False))

    if args.check:
        return runtime_check()

    if args.filename:
        sys.argv = [sys.argv[0], args.filename]
    else:
        sys.argv = [sys.argv[0]]
        if koko.BUNDLED:
            os.chdir(Path.home())

    try:
        import wx
        from koko.app import App
    except ImportError as exc:
        print(f"kokopelli could not start: {exc}", file=sys.stderr)
        print("Install the project dependencies with `uv sync`.", file=sys.stderr)
        return 1

    wx.Log.EnableLogging(False)
    app = App()
    app.MainLoop()
    return 0
