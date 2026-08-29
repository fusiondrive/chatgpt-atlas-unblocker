#!/bin/bash

PLIST_NAME="com.openai.atlas.unblocker.plist"
TARGET_PLIST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "=== Uninstalling ChatGPT Atlas Unblocker ==="

# 1. Unload and remove launchd service
launchctl unload "$TARGET_PLIST" 2>/dev/null || true
rm -f "$TARGET_PLIST"
pkill -f atlas_unblocker.py 2>/dev/null || true

# 2. Disable proxy on all network services
networksetup -listallnetworkservices 2>/dev/null | while read -r service; do
    if [[ -n "$service" && "$service" != *"asterisk"* ]]; then
        networksetup -setwebproxystate "$service" off 2>/dev/null || true
        networksetup -setsecurewebproxystate "$service" off 2>/dev/null || true
    fi
done

# 3. Clean up user defaults
for domain in com.openai.atlas com.openai.chat com.openai.codex; do
    defaults delete "$domain" com.openai.pinned_cert_hash_list 2>/dev/null || true
done

# 4. Remove trusted cert from Keychain
security delete-certificate -c "ios.chat.openai.com" "$HOME/Library/Keychains/login.keychain-db" 2>/dev/null || true

# 5. Remove data directory
rm -rf "$HOME/.chatgpt-atlas-unblocker"

echo "[+] ChatGPT Atlas Unblocker completely uninstalled."
