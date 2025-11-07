#!/usr/bin/env bash
set -e
mkdir -p logs
python test_runner.py | tee logs/test_run.log
exit ${PIPESTATUS[0]}
