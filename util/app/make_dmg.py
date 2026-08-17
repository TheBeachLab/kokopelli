#!/usr/bin/env python3
"""Create a polished drag-to-Applications macOS disk image."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import plistlib
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont


BACKGROUND_SIZE = (660, 400)
APP_POSITION = (165, 215)
APPLICATIONS_POSITION = (495, 215)
WINDOW_BOUNDS = (100, 100, 760, 500)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description=("Create, sign, optionally notarize, and validate a drag-to-Applications DMG.")
    )
    command.add_argument("app", type=Path, help="path to the signed .app bundle")
    command.add_argument("--output", type=Path, help="output .dmg path")
    command.add_argument("--volume-name", help="Finder volume name; defaults to the app name")
    command.add_argument("--identity", help="Developer ID Application identity for the DMG")
    command.add_argument(
        "--profile",
        help="notarytool credentials profile stored in the macOS Keychain",
    )
    command.add_argument("--force", action="store_true", help="replace an existing DMG")
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


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        "/System/Library/Fonts/SFNSRounded.ttf" if bold else "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def create_background(target: Path, app_name: str) -> None:
    width, height = BACKGROUND_SIZE
    image = Image.new("RGB", BACKGROUND_SIZE)
    pixels = image.load()
    for y in range(height):
        blend = y / max(height - 1, 1)
        color = tuple(
            round(start + (end - start) * blend)
            for start, end in zip((247, 249, 252), (224, 231, 241))
        )
        for x in range(width):
            pixels[x, y] = color

    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (18, 18, width - 18, height - 18), radius=24, outline=(255, 255, 255), width=2
    )

    title = f"Install {app_name}"
    title_font = font(30, bold=True)
    subtitle_font = font(16)
    title_box = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_box[2] - title_box[0]
    draw.text(((width - title_width) / 2, 38), title, fill=(29, 38, 52), font=title_font)

    subtitle = "Drag the app to Applications"
    subtitle_box = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_box[2] - subtitle_box[0]
    draw.text(
        ((width - subtitle_width) / 2, 82),
        subtitle,
        fill=(84, 96, 113),
        font=subtitle_font,
    )

    arrow_y = 215
    draw.line((275, arrow_y + 5, 405, arrow_y + 5), fill=(157, 171, 191), width=20)
    draw.polygon(
        ((398, arrow_y - 30), (450, arrow_y + 5), (398, arrow_y + 40)), fill=(157, 171, 191)
    )
    draw.line((275, arrow_y, 405, arrow_y), fill=(38, 118, 255), width=16)
    draw.polygon(((398, arrow_y - 34), (450, arrow_y), (398, arrow_y + 34)), fill=(38, 118, 255))

    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG", optimize=True)


def app_icon(app: Path) -> Path | None:
    resources = app / "Contents" / "Resources"
    info_path = app / "Contents" / "Info.plist"
    if info_path.is_file():
        with info_path.open("rb") as source:
            icon_name = plistlib.load(source).get("CFBundleIconFile")
        if icon_name:
            icon_path = resources / icon_name
            if not icon_path.suffix:
                icon_path = icon_path.with_suffix(".icns")
            if icon_path.is_file():
                return icon_path
    return next(iter(sorted(resources.glob("*.icns"))), None)


def apple_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def configure_finder(volume_name: str, app_name: str) -> None:
    left, top, right, bottom = WINDOW_BOUNDS
    app_x, app_y = APP_POSITION
    applications_x, applications_y = APPLICATIONS_POSITION
    script = f"""
tell application "Finder"
    tell disk {apple_string(volume_name)}
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set pathbar visible of container window to false
        set bounds of container window to {{{left}, {top}, {right}, {bottom}}}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 128
        set text size of viewOptions to 14
        set background picture of viewOptions to file ".background:background.png"
        set position of item {apple_string(app_name)} to {{{app_x}, {app_y}}}
        set position of item "Applications" to {{{applications_x}, {applications_y}}}
        update without registering applications
        delay 2
        close container window
    end tell
end tell
"""
    run("osascript", "-e", script)


def mount(image: Path, mountpoint: Path, *, readonly: bool) -> None:
    mode = "-readonly" if readonly else "-readwrite"
    run(
        "hdiutil",
        "attach",
        image,
        mode,
        "-noverify",
        "-noautoopen",
        "-nobrowse",
        "-mountpoint",
        mountpoint,
    )


def mount_for_finder(image: Path) -> Path:
    result = run(
        "hdiutil",
        "attach",
        image,
        "-readwrite",
        "-noverify",
        "-noautoopen",
        "-plist",
        capture=True,
    )
    details = plistlib.loads(result.stdout.encode())
    for entity in details.get("system-entities", []):
        mountpoint = entity.get("mount-point")
        if mountpoint:
            return Path(mountpoint)
    raise SystemExit("hdiutil did not report a mounted volume")


def detach(mountpoint: Path) -> None:
    run("hdiutil", "detach", mountpoint)


def create_dmg(app: Path, output: Path, volume_name: str, force: bool) -> None:
    if output.exists():
        if not force:
            raise SystemExit(f"Output already exists: {output}; pass --force to replace it")
        output.unlink()
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="macos-dmg-") as temporary:
        root = Path(temporary)
        staging = root / "staging"
        staging.mkdir()
        run("ditto", app, staging / app.name)
        os.symlink("/Applications", staging / "Applications")
        create_background(staging / ".background" / "background.png", app.stem)
        icon = app_icon(app)
        if icon:
            run("ditto", icon, staging / ".VolumeIcon.icns")

        size_kib = int(run("du", "-sk", staging, capture=True).stdout.split()[0])
        image_size_kib = max(size_kib + 32768, round(size_kib * 1.2))
        writable = root / "writable.dmg"
        run(
            "hdiutil",
            "create",
            "-ov",
            "-size",
            f"{image_size_kib}k",
            "-fs",
            "HFS+",
            "-volname",
            volume_name,
            "-srcfolder",
            staging,
            "-format",
            "UDRW",
            writable,
        )

        expected_mountpoint = Path("/Volumes") / volume_name
        if expected_mountpoint.exists():
            raise SystemExit(f"A volume is already mounted at {expected_mountpoint}")
        mountpoint = mount_for_finder(writable)
        if mountpoint != expected_mountpoint:
            detach(mountpoint)
            raise SystemExit(
                f"Expected Finder volume {expected_mountpoint}, but hdiutil used {mountpoint}"
            )
        try:
            run("SetFile", "-a", "V", mountpoint / ".background")
            if (mountpoint / ".VolumeIcon.icns").is_file():
                run("SetFile", "-a", "V", mountpoint / ".VolumeIcon.icns")
                run("SetFile", "-a", "C", mountpoint)
            configure_finder(volume_name, app.name)
            run("sync")
        finally:
            detach(mountpoint)

        run(
            "hdiutil",
            "convert",
            writable,
            "-format",
            "UDZO",
            "-imagekey",
            "zlib-level=9",
            "-o",
            output,
        )


def sign_dmg(dmg: Path, identity: str) -> None:
    run("codesign", "--force", "--sign", identity, "--timestamp", dmg)
    run("codesign", "--verify", "--verbose=2", dmg)


def notarize_dmg(dmg: Path, profile: str) -> None:
    result = run(
        "xcrun",
        "notarytool",
        "submit",
        dmg,
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
            run("xcrun", "notarytool", "log", submission_id, "--keychain-profile", profile)
        raise SystemExit(f"Apple notarization did not succeed: {status}")

    if submission_id:
        log = run(
            "xcrun",
            "notarytool",
            "log",
            submission_id,
            "--keychain-profile",
            profile,
            capture=True,
        )
        issues = json.loads(log.stdout).get("issues", [])
        if issues:
            print("Apple notarization log contains issues:")
            print(json.dumps(issues, indent=2))

    run("xcrun", "stapler", "staple", dmg)
    run("xcrun", "stapler", "validate", dmg)
    run(
        "spctl",
        "--assess",
        "--type",
        "open",
        "--context",
        "context:primary-signature",
        "--verbose=4",
        dmg,
    )


def validate_dmg(dmg: Path, app_name: str) -> None:
    run("hdiutil", "verify", dmg)
    with tempfile.TemporaryDirectory(prefix="macos-dmg-check-") as temporary:
        mountpoint = Path(temporary) / "mount"
        mountpoint.mkdir()
        mount(dmg, mountpoint, readonly=True)
        try:
            bundled_app = mountpoint / app_name
            applications = mountpoint / "Applications"
            if not bundled_app.is_dir():
                raise SystemExit(f"DMG is missing {app_name}")
            if not applications.is_symlink() or os.readlink(applications) != "/Applications":
                raise SystemExit("DMG is missing the Applications link")
            if not (mountpoint / ".background" / "background.png").is_file():
                raise SystemExit("DMG is missing its installation background")
            if not (mountpoint / ".DS_Store").is_file():
                raise SystemExit("DMG is missing its Finder layout")
            run("codesign", "--verify", "--deep", "--strict", "--verbose=2", bundled_app)
        finally:
            detach(mountpoint)


def main() -> int:
    args = parser().parse_args()
    if platform.system() != "Darwin":
        raise SystemExit("DMG creation must run on macOS")

    app = args.app.resolve()
    if app.suffix != ".app" or not app.is_dir():
        raise SystemExit(f"Not an application bundle: {app}")
    if args.profile and not args.identity:
        raise SystemExit("--identity is required when --profile is used")

    output = args.output.resolve() if args.output else app.with_name(f"{app.stem}-macOS.dmg")
    if output.suffix != ".dmg":
        raise SystemExit(f"Output must use the .dmg extension: {output}")
    volume_name = args.volume_name or app.stem

    run("codesign", "--verify", "--deep", "--strict", "--verbose=2", app)
    create_dmg(app, output, volume_name, args.force)
    if args.identity:
        sign_dmg(output, args.identity)
    if args.profile:
        notarize_dmg(output, args.profile)
    if args.identity:
        run("codesign", "--verify", "--verbose=2", output)
    validate_dmg(output, app.name)

    print(f"Drag-to-Applications disk image: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
