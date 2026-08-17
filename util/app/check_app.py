#!/usr/bin/env python3
"""Validate the structure, signature, architecture, and runtime of Kokopelli.app."""

from __future__ import annotations

from pathlib import Path
import plistlib
import platform
import subprocess
import sys


EXPECTED_IDENTIFIER = "org.thebeachlab.kokopelli"


def run(*command: str | Path) -> None:
    subprocess.run([str(part) for part in command], check=True)


def main(argv: list[str]) -> int:
    if platform.system() != "Darwin":
        raise SystemExit("Kokopelli.app validation requires macOS")

    app = Path(argv[1] if len(argv) > 1 else "dist/Kokopelli.app").resolve()
    plist_path = app / "Contents" / "Info.plist"
    executable = app / "Contents" / "MacOS" / "Kokopelli"
    library = app / "Contents" / "Frameworks" / "libfab" / "libfab.dylib"
    resources = app / "Contents" / "Resources"
    required_files = (
        plist_path,
        executable,
        library,
        resources / "ko.icns",
        resources / "examples" / "gear.ko",
        resources / "Documentation" / "README.md",
        resources / "dottext.py",
    )
    for required in required_files:
        if not required.exists():
            raise SystemExit(f"Missing bundle component: {required}")

    with plist_path.open("rb") as source:
        info = plistlib.load(source)
    if info.get("CFBundleIdentifier") != EXPECTED_IDENTIFIER:
        raise SystemExit("Unexpected CFBundleIdentifier")
    if info.get("CFBundleExecutable") != "Kokopelli":
        raise SystemExit("Unexpected CFBundleExecutable")
    declarations = info.get("UTImportedTypeDeclarations", [])
    if not any(
        declaration.get("UTTypeIdentifier") == "org.thebeachlab.kokopelli.design"
        for declaration in declarations
    ):
        raise SystemExit("Kokopelli document type is not registered")

    run("plutil", "-lint", plist_path)
    run("codesign", "--verify", "--deep", "--strict", "--verbose=2", app)
    run("file", executable)
    run("file", library)
    run(executable, "--check")
    print(f"Validated {app}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
