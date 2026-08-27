#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_NAME="com.openai.atlas.unblocker.plist"
TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"
PYTHON_BIN="$(which python3)"

echo "=== Installing ChatGPT Atlas Unblocker ==="

# 1. Update plist paths
mkdir -p "$HOME/Library/LaunchAgents"
sed -e "s|/usr/bin/python3|$PYTHON_BIN|g" \
    -e "s|/Users/steve/chatgpt-atlas-unblocker|$SCRIPT_DIR|g" \
    -e "s|/Users/steve/.chatgpt-atlas-unblocker|$HOME/.chatgpt-atlas-unblocker|g" \
    "$SCRIPT_DIR/$PLIST_NAME" > "$TARGET_PLIST"

# 2. Stop previous instance if running
launchctl unload "$TARGET_PLIST" 2>/dev/null || true
pkill -f atlas_unblocker.py 2>/dev/null || true

# 3. Load service
launchctl load "$TARGET_PLIST"
echo "[+] Background service loaded successfully."
echo "[+] ChatGPT Atlas is ready to use!"
