#!/bin/bash
set -e

APP_PATH="/Applications/ChatGPT Atlas.app"
AURA_PATH="$APP_PATH/Contents/Frameworks/Aura.framework/Versions/A/Aura"

echo "=== Restoring original ChatGPT Atlas binary ==="
if [ -f "$AURA_PATH.original" ]; then
    cp "$AURA_PATH.original" "$AURA_PATH"
    codesign --force --deep -s - "$APP_PATH"
    echo "[+] Original binary restored successfully."
else
    echo "[-] No original backup found at $AURA_PATH.original."
fi
