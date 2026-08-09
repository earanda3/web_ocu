#!/usr/bin/env bash
# Production build step: minify JS/CSS in place and cache-bust the HTML references.
#
# Run by the deploy workflow AFTER checkout, BEFORE the FTP upload, so the source
# in git stays readable while the server gets minified assets. Safe because esbuild
# minifies WITHOUT bundling: top-level/global names are preserved, so the classic
# scripts (app.js, app-init.js, the ui viewers) still share globals exactly as before.
#
# Usage: scripts/build_minify.sh <cache-bust-version>   (e.g. the short git SHA)
set -euo pipefail
VER="${1:-dev}"

JS_FILES=(
  js/app.js js/app-init.js
  js/ui/stl-viewer.js js/ui/info-viewer.js js/ui/tecla-viewer.js js/ui/screenshot.js
  js/tecla-device.js js/tecla-modes.js js/tecla-simulator.js js/tecla-webmidi.js
  vendor/three/GLTFLoader.js vendor/three/DRACOLoader.js
)
CSS_FILES=(css/style.css vendor/pdf-viewer.css)

echo "Minifying JS…"
for f in "${JS_FILES[@]}"; do
  [ -f "$f" ] || { echo "  skip (missing): $f"; continue; }
  before=$(wc -c < "$f")
  npx --yes esbuild@0.24 "$f" --minify --allow-overwrite --outfile="$f" >/dev/null 2>&1
  after=$(wc -c < "$f")
  printf "  %-34s %7d -> %7d bytes\n" "$f" "$before" "$after"
done

echo "Minifying CSS…"
for f in "${CSS_FILES[@]}"; do
  [ -f "$f" ] || { echo "  skip (missing): $f"; continue; }
  npx --yes esbuild@0.24 "$f" --minify --loader:.css=css --allow-overwrite --outfile="$f" >/dev/null 2>&1
  echo "  $f minified"
done

echo "Cache-busting HTML references (?v=$VER)…"
for html in index.html tecla.html about.html; do
  [ -f "$html" ] || continue
  # Append ?v=VER to local js/css refs that don't already carry a query string.
  sed -i.bak -E "s#(src|href)=\"(js/[^\"?]+\.js|css/[^\"?]+\.css|vendor/[^\"?]+\.(js|css))\"#\1=\"\2?v=$VER\"#g" "$html"
  rm -f "$html.bak"
  echo "  $html"
done

echo "Build done."
