#!/usr/bin/env bash
set -euo pipefail

SOURCE="${1:-public/hero.mp4}"
OUT_DIR="${2:-public}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required." >&2
  exit 1
fi

if [[ ! -f "$SOURCE" ]]; then
  echo "Source video not found: $SOURCE" >&2
  echo "Place the supplied hero.mp4 at public/hero.mp4, then rerun this script." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

# Desktop: visually strong but capped to 1440px wide, H.264 baseline compatibility.
ffmpeg -y -i "$SOURCE" -an \
  -vf "fps=30,scale='min(1440,iw)':-2:flags=lanczos" \
  -c:v libx264 -preset slow -crf 23 -profile:v high -level 4.1 \
  -movflags +faststart -pix_fmt yuv420p \
  "$OUT_DIR/hero-desktop.mp4"

# Mobile: narrower encode to avoid shipping desktop bitrate to small screens.
ffmpeg -y -i "$SOURCE" -an \
  -vf "fps=30,scale='min(900,iw)':-2:flags=lanczos" \
  -c:v libx264 -preset slow -crf 25 -profile:v high -level 4.0 \
  -movflags +faststart -pix_fmt yuv420p \
  "$OUT_DIR/hero-mobile.mp4"

# Poster at ~35% of the source duration; crop/position remains handled in CSS.
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$SOURCE")
STAMP=$(awk -v d="$DURATION" 'BEGIN { printf "%.3f", d*0.35 }')
ffmpeg -y -ss "$STAMP" -i "$SOURCE" -frames:v 1 -update 1 -vf "scale='min(1600,iw)':-2:flags=lanczos" -q:v 3 "$OUT_DIR/hero-poster.jpg"

echo "Created: hero-desktop.mp4, hero-mobile.mp4, hero-poster.jpg"
