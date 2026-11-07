#!/bin/bash
set -u
mkdir -p /logs/verifier
python3 /tests/score.py || true
if [ ! -s /logs/verifier/reward.txt ]; then
  echo 0 > /logs/verifier/reward.txt
fi
exit 0
