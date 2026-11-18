#!/bin/bash
# Run on an Apple Silicon Mac with Xcode Command Line Tools and a Rust toolchain.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ "$(uname -sm)" == "Darwin arm64" ]] || { echo "需要 Apple Silicon Mac" >&2; exit 1; }
python_bin="${PYTHON:-.venv/bin/python}"
[[ -f frontend/dist/index.html ]] || { echo "请先在 frontend 目录安装依赖并执行 build" >&2; exit 1; }
"$python_bin" scripts/content_manifest.py --check
"$python_bin" -m PyInstaller --clean --noconfirm --onefile --name jzs-engine \
  --workpath .artifacts/pyi/work --distpath .artifacts/pyi/dist --specpath .artifacts/pyi \
  --add-data "$PWD/PARAMETER_REGISTRY.json:." \
  --hidden-import uvicorn.lifespan.on --hidden-import uvicorn.protocols.http.h11_impl \
  --hidden-import uvicorn.loops.asyncio main.py
cargo build --locked --release --manifest-path src-tauri/Cargo.toml
mkdir -p release
stage="$(mktemp -d "$PWD/release/.stage.XXXXXX")"
trap 'rm -rf "$stage"' EXIT
app="$stage/局中事.app"
mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
cp src-tauri/target/release/juzhongshi .artifacts/pyi/dist/jzs-engine "$app/Contents/MacOS/"
cp -R frontend/dist "$app/Contents/Resources/web"
cp src-tauri/icons/game.icns "$app/Contents/Resources/"
"$python_bin" scripts/package_notices.py "$app/Contents/Resources/THIRD_PARTY_NOTICES.txt"
cp src-tauri/Info.plist "$app/Contents/"
"$python_bin" scripts/macos_minimum.py "$app"
codesign -s - --force "$app/Contents/MacOS/jzs-engine"
codesign -s - --force "$app"
codesign --verify --deep --strict "$app"
# Replace only our reproducible build output, after verification.
ditto -c -k --sequesterRsrc --keepParent "$app" "$stage/局中事-macOS-arm64.zip"
if [[ -d release/局中事.app ]]; then mv release/局中事.app "$stage/previous.app"; fi
mv "$app" release/
mv "$stage/局中事-macOS-arm64.zip" release/
(
  cd release
  shopt -s nullglob
  shasum -a 256 局中事-*.zip 局中事-*.tar.gz > "$stage/SHA256SUMS.txt"
  mv "$stage/SHA256SUMS.txt" .
)
