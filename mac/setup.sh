#!/bin/sh
# macOS setup: builds the Apple Vision OCR helper and the Python environment.
set -eu
cd "$(dirname "$0")/.."
if [ "$(uname -s)" != Darwin ]; then
  echo 'Bu kurulum macOS içindir. Windows için Kurulum.bat kullan.' >&2
  exit 1
fi
mkdir -p .build
swiftc -module-cache-path .build/module-cache mac/vision.swift -o .build/yula-vision
python3 -m venv .venv
.venv/bin/python -m pip install -r mac/requirements.txt
echo 'Kurulum tamam. Paneli açmak için mac/Yula-Panel.command dosyasına çift tıkla.'
