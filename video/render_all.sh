#!/usr/bin/env bash
# Render every shot of STARBRICK to PNG frames (resumable: finished frames are skipped).
# Usage: video/render_all.sh [samples] [python-with-bpy]
set -euo pipefail
cd "$(dirname "$0")/.."
SAMPLES=${1:-28}
PY=${2:-python}
for shot in 1 2 3 4 5; do
  echo "== shot $shot =="
  "$PY" video/starbrick.py --shot "$shot" --out "renders/shot$shot" --samples "$SAMPLES"
done
