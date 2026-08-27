#!/bin/bash

PLIST_NAME="com.openai.atlas.unblocker.plist"
TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "=== Uninstalling ChatGPT Atlas Unblocker ==="

launchctl unload "$TARGET_PLIST" 2>/dev/null || true
rm -f "$TARGET_PLIST"
pkill -f atlas_unblocker.py 2>/dev/null || true

networksetup -setwebproxystate "Wi-Fi" "off" 2>/dev/null || true
networksetup -setsecurewebproxystate "Wi-Fi" "off" 2>/dev/null || true

security delete-certificate -c "ios.chat.openai.com" "$HOME/Library/Keychains/login.keychain-db" 2>/dev/null || true

echo "[+] Uninstalled and proxy settings restored."
