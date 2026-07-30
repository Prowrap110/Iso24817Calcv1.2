#!/bin/bash

set -euo pipefail

REPOSITORY_DIRECTORY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VIRTUAL_ENVIRONMENT="$REPOSITORY_DIRECTORY/.venv-desktop"
APPLICATION_BUNDLE="$REPOSITORY_DIRECTORY/dist/PROWRAP ISO 24817 Calculator.app"
MAIN_EXECUTABLE="$APPLICATION_BUNDLE/Contents/MacOS/PROWRAP ISO 24817 Calculator"
INFO_PLIST="$APPLICATION_BUNDLE/Contents/Info.plist"
ARCHIVE="$REPOSITORY_DIRECTORY/release/PROWRAP-Calculator-macOS-arm64-M4-M5.zip"
DRY_RUN=false

if [[ $# -gt 1 ]] || [[ $# -eq 1 && "$1" != "--dry-run" ]]; then
    echo "usage: $0 [--dry-run]" >&2
    exit 2
fi
if [[ $# -eq 1 ]]; then
    DRY_RUN=true
fi

cd "$REPOSITORY_DIRECTORY"

if [[ "$DRY_RUN" == true ]]; then
    UNAME_MACHINE="${PROWRAP_DRY_RUN_UNAME_MACHINE:-$(uname -m)}"
    PYTHON_MACHINE="${PROWRAP_DRY_RUN_PYTHON_MACHINE:-$(python3 -c 'import platform; print(platform.machine())')}"
else
    UNAME_MACHINE="$(uname -m)"
    PYTHON_MACHINE="$(python3 -c 'import platform; print(platform.machine())')"
fi

python3 -c \
    'from packaging_contract import require_arm64; import sys; require_arm64(uname_machine=sys.argv[1], python_machine=sys.argv[2])' \
    "$UNAME_MACHINE" "$PYTHON_MACHINE"

run_gate() {
    local gate_name="$1"
    shift
    if [[ "$DRY_RUN" == true ]]; then
        printf '[gate] %s\n' "$gate_name"
        return 0
    fi
    printf '[gate] %s\n' "$gate_name"
    "$@"
}

inspect_architecture() {
    local description
    description="$(file "$MAIN_EXECUTABLE")"
    printf '%s\n' "$description"
    if [[ "$description" != *arm64* ]]; then
        echo "main executable is not arm64: $description" >&2
        return 1
    fi
}

inspect_bundle_metadata() {
    local actual
    local key
    local expected
    while [[ $# -gt 0 ]]; do
        key="$1"
        expected="$2"
        shift 2
        actual="$(plutil -extract "$key" raw -o - "$INFO_PLIST")"
        if [[ "$actual" != "$expected" ]]; then
            echo "$key mismatch: expected $expected, observed $actual" >&2
            return 1
        fi
    done
}

if [[ "$DRY_RUN" == true ]]; then
    run_gate "full test suite" true
    run_gate "PyInstaller build" true
    run_gate "architecture inspection" true
    run_gate "bundle metadata inspection" true
    run_gate "signature verification" true
    run_gate "ZIP creation" true
    exit 0
fi

if [[ ! -d "$VIRTUAL_ENVIRONMENT" ]]; then
    python3 -m venv "$VIRTUAL_ENVIRONMENT"
fi
PYTHON="$VIRTUAL_ENVIRONMENT/bin/python"
"$PYTHON" -m pip install --upgrade pip setuptools wheel
"$PYTHON" -m pip install -r "$REPOSITORY_DIRECTORY/requirements-desktop.txt"

run_gate "full test suite" "$PYTHON" -m unittest discover -v

rm -rf \
    "$REPOSITORY_DIRECTORY/build" \
    "$REPOSITORY_DIRECTORY/dist" \
    "$REPOSITORY_DIRECTORY/release"

run_gate \
    "PyInstaller build" \
    "$PYTHON" -m PyInstaller --clean --noconfirm "$REPOSITORY_DIRECTORY/PROWRAPCalculator.spec"
run_gate "architecture inspection" inspect_architecture
run_gate \
    "bundle metadata inspection" \
    inspect_bundle_metadata \
    CFBundleIdentifier com.protapglobal.prowrap.iso24817calculator \
    CFBundleShortVersionString 1.1 \
    LSMinimumSystemVersion 12.0
run_gate "signature verification" codesign --verify --deep --strict "$APPLICATION_BUNDLE"

mkdir -p "$REPOSITORY_DIRECTORY/release"
run_gate \
    "ZIP creation" \
    ditto -c -k --sequesterRsrc --keepParent "$APPLICATION_BUNDLE" "$ARCHIVE"
