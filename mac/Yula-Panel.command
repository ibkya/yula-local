#!/bin/sh
# Opens the Yula panel on macOS. First run builds the OCR helper and Python environment.
cd "$(dirname "$0")/.." || exit 1
if [ ! -x .venv/bin/python ] || [ ! -x .build/yula-vision ]; then
  sh mac/setup.sh || exit 1
fi
exec .venv/bin/python app/panel.py
