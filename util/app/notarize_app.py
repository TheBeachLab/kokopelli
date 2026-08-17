#!/usr/bin/env python3
"""Submit any properly signed macOS application to Apple's notary service."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import subprocess
import tempfile


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description=(
            "Verify, notarize, staple, and archive a Developer ID-signed macOS application."
        )
    )
    command.add_argument("app", type=Path, help="path to the signed .app bundle")
    command.add_argument(
        "--profile",
        help="notarytool credentials profile stored in the macOS Keychain",
    )
    command.add_argument("--output", type=Path, help="final ZIP path; defaults beside the app")
    command.add_argument("--force", action="store_true", help="replace an existing output ZIP")
    command.add_argument(
        "--verify-only",
        action="store_true",
        help="validate the distribution signature without submitting the app",
    )
    return command


def run(
    *command: str | Path,
    capture: bool = False,
) -> subprocess.CompletedProcess[str]:
    printable = " ".join(str(part) for part in command)
    print(f"+ {printable}", flush=True)
    try:
        return subprocess.run(
            [str(part) for part in command],
            check=True,
            capture_output=capture,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        if error.stdout:
            print(error.stdout, end="")
        if error.stderr:
            print(error.stderr, end="")
        raise SystemExit(f"Command failed with exit status {error.returncode}: {printable}")


def signature_details(app: Path) -> str:
    result = run("codesign", "-d", "--verbose=4", app, capture=True)
    return result.stdout + result.stderr


def verify_distribution_signature(app: Path) -> None:
    run("codesign", "--verify", "--deep", "--strict", "--verbose=2", app)
    details = signature_details(app)
    requirements = {
        "Developer ID identity": "Authority=Developer ID Application:",
        "Hardened Runtime": "runtime",
    }
    missing = [label for label, marker in requirements.items() if marker not in details]
    if "TeamIdentifier=not set" in details:
        missing.append("Apple developer team identifier")
    if missing:
        raise SystemExit("App is not distribution-ready; missing " + ", ".join(missing))


def archive(app: Path, target: Path) -> None:
    run("ditto", "-c", "-k", "--keepParent", app, target)
    run("unzip", "-tq", target)


def notarize(app: Path, profile: str, output: Path, force: bool) -> None:
    if output.exists():
        if not force:
            raise SystemExit(f"Output already exists: {output}; pass --force to replace it")
        output.unlink()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="macos-notary-") as temporary:
        submission = Path(temporary) / f"{app.stem}.zip"
        archive(app, submission)
        result = run(
            "xcrun",
            "notarytool",
            "submit",
            submission,
            "--keychain-profile",
            profile,
            "--wait",
            "--output-format",
            "json",
            capture=True,
        )
        response = json.loads(result.stdout)
        status = response.get("status")
        submission_id = response.get("id")
        print(f"Apple submission {submission_id}: {status}")
        if status != "Accepted":
            if submission_id:
                run(
                    "xcrun",
                    "notarytool",
                    "log",
                    submission_id,
                    "--keychain-profile",
                    profile,
                )
            raise SystemExit(f"Apple notarization did not succeed: {status}")

    run("xcrun", "stapler", "staple", app)
    run("xcrun", "stapler", "validate", app)
    run("spctl", "--assess", "--type", "execute", "--verbose=4", app)
    archive(app, output)


def main() -> int:
    args = parser().parse_args()
    if platform.system() != "Darwin":
        raise SystemExit("macOS notarization must run on macOS")

    app = args.app.resolve()
    if app.suffix != ".app" or not app.is_dir():
        raise SystemExit(f"Not an application bundle: {app}")
    output = args.output.resolve() if args.output else app.with_name(f"{app.stem}-notarized.zip")

    verify_distribution_signature(app)
    if args.verify_only:
        print(f"Distribution signature verified: {app}")
        return 0
    if not args.profile:
        raise SystemExit("--profile is required unless --verify-only is used")
    notarize(app, args.profile, output, args.force)
    print(f"Notarized application: {app}")
    print(f"Distributable archive: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
