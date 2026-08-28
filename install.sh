#!/bin/bash
set -e

echo "=== ChatGPT Atlas Sunset Patcher ==="
python3 "$(dirname "$0")/patch_atlas.py"
echo "=== Done! You can now launch ChatGPT Atlas normally. ==="
