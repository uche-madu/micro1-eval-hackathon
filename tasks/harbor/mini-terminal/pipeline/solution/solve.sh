#!/bin/bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$HERE/fixed_pipeline.py" /workspace/pipeline.py
