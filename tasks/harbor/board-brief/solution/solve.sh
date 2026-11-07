#!/bin/bash
set -euo pipefail
mkdir -p /output
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$HERE/reference_brief.md" /output/brief.md
cp "$HERE/reference_findings.json" /output/findings.json
