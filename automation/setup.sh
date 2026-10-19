#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ "$(uname -s)" != Darwin ]; then
  echo 'Bu görsel otomasyon sürümü macOS içindir.' >&2
  exit 1
fi
mkdir -p .build
swiftc -module-cache-path .build/module-cache automation/vision.swift -o .build/yula-vision
python3 -m venv .venv
.venv/bin/python -m pip install -r automation/requirements.txt
echo 'Kurulum tamam. İnceleme: npm run bot. Canlı: npm run bot -- --live'
