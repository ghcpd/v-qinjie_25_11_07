#!/usr/bin/env bash
set -e
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Setup complete"
