#!/usr/bin/env bash
set -e
python test_runner.py "$@" | tee -a logs/test_run.log
