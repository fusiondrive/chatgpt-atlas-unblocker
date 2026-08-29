#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$(which python3)"

echo "=== ChatGPT Atlas Sunset Patcher ==="
"$PYTHON_BIN" "$SCRIPT_DIR/patch_atlas.py"
echo "=== Done! You can now launch ChatGPT Atlas normally. ==="
