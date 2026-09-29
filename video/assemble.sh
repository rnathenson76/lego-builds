#!/usr/bin/env bash
# Cut the rendered shots together: 2.39:1 letterbox in 1280x720, fade in/out,
# light film grain, H.264.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=${1:-video/starbrick.mp4}
inputs=(); filt=""
for i in 1 2 3 4 5; do
  inputs+=(-framerate 24 -i "renders/shot$i/%04d.png")
  filt+="[$((i-1)):v]"
done
ffmpeg -y "${inputs[@]}" -filter_complex \
  "${filt}concat=n=5:v=1:a=0,pad=1280:720:0:92:black,\
fade=t=in:st=0:d=0.6,fade=t=out:st=19.3:d=0.7,\
noise=c0s=5:c0f=t+u,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -preset slow -crf 16 -movflags +faststart "$OUT"
