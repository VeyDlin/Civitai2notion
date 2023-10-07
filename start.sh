#!/bin/bash
set -e

if [ ! -d ".venv" ]; then
    echo "First install..."

    python3 -m venv .venv
    source "./.venv/bin/activate"
    pip install -r requirements.txt
else
    source "./.venv/bin/activate"
fi

python3 main.py
