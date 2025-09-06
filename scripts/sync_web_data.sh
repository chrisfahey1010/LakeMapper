#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
WEB_DIR="$ROOT_DIR/web/public/output"

mkdir -p "$WEB_DIR"

rsync -a --delete \
  "$ROOT_DIR/output/" \
  "$WEB_DIR/"

echo "Synced output → web/public/output"

