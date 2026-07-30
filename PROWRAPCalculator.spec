from pathlib import Path

from PyInstaller.utils.hooks import collect_all

from packaging_contract import discover_packaging_inputs, packaging_metadata


PROJECT_DIRECTORY = Path(SPECPATH)
METADATA = packaging_metadata()
INPUTS = discover_packaging_inputs(PROJECT_DIRECTORY, collect_all=collect_all)


analysis = Analysis(
    [METADATA["entry_point"]],
    pathex=[str(PROJECT_DIRECTORY)],
    binaries=INPUTS.binaries,
    datas=INPUTS.datas,
    hiddenimports=INPUTS.hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

python_archive = PYZ(analysis.pure)

executable = EXE(
    python_archive,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="PROWRAP ISO 24817 Calculator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    argv_emulation=False,
    target_arch=METADATA["target_arch"],
    codesign_identity=None,
    entitlements_file=None,
)

collected = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="PROWRAP ISO 24817 Calculator",
)

application = BUNDLE(
    collected,
    name="PROWRAP ISO 24817 Calculator.app",
    icon=None,
    bundle_identifier=METADATA["bundle_id"],
    version="1.1",
    info_plist={
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
    },
)
