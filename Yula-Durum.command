#!/bin/sh
cd "$(dirname "$0")" || exit 1
exec .venv/bin/python automation/status_window.py
