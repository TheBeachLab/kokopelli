# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


ROOT = Path(SPECPATH).parents[1]
ICON = ROOT / "util" / "app" / "ko.icns"
LIBRARY_SOURCES = [(str(path), ".") for path in sorted((ROOT / "koko" / "lib").glob("*.py"))]

a = Analysis(
    [str(ROOT / "koko" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[(str(ROOT / "libfab" / "libfab.dylib"), "libfab")],
    datas=[
        (str(ROOT / "examples"), "examples"),
        (str(ROOT / "README.md"), "Documentation"),
        (str(ROOT / "LICENSE.md"), "Documentation"),
        (str(ROOT / "THIRD_PARTY_NOTICES.md"), "Documentation"),
        *LIBRARY_SOURCES,
    ],
    hiddenimports=[*collect_submodules("koko.lib"), "PIL"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "ruff"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Kokopelli",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[str(ICON)],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Kokopelli",
)
app = BUNDLE(
    coll,
    name="Kokopelli.app",
    icon=str(ICON),
    bundle_identifier="org.thebeachlab.kokopelli",
    version="0.3.0",
    info_plist={
        "CFBundleDisplayName": "Kokopelli",
        "CFBundleName": "Kokopelli",
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeName": "Kokopelli Design",
                "CFBundleTypeRole": "Editor",
                "LSHandlerRank": "Owner",
                "LSItemContentTypes": ["org.thebeachlab.kokopelli.design"],
            }
        ],
        "UTImportedTypeDeclarations": [
            {
                "UTTypeIdentifier": "org.thebeachlab.kokopelli.design",
                "UTTypeDescription": "Kokopelli Design",
                "UTTypeConformsTo": ["public.source-code"],
                "UTTypeTagSpecification": {
                    "public.filename-extension": ["ko"],
                    "public.mime-type": "text/x-kokopelli",
                },
            }
        ],
        "LSApplicationCategoryType": "public.app-category.graphics-design",
        "NSHighResolutionCapable": True,
        "NSPrincipalClass": "NSApplication",
    },
)
