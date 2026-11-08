#!/bin/bash
set -euo pipefail
mkdir -p /output
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$HERE/reference_decision.json" /output/decision.json
