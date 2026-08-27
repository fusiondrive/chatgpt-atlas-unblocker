# ChatGPT Atlas Sunset & Deprecation Unblocker

A lightweight, zero-side-effect network hook daemon to eliminate the full-screen deprecation/sunset blocking modal in OpenAI's **ChatGPT Atlas** macOS application while preserving 100% official Apple Developer ID code signatures, Apple App Attest / DeviceCheck hardware verification, and Keychain session persistence.

---

## Background & Technical Root Cause

1. **The Sunset Mechanism**:
   - When ChatGPT Atlas launches, its internal `Aura.framework` queries:
     `GET https://ios.chat.openai.com/public-api/mobile/app_support_status/v1`
   - When OpenAI returns `{"status": "hard_deprecation"}`, the SwiftUI layer renders an unclosable full-screen card dialog (`BrowserSunsetDialogView`) blocking all interactions and prompting the user to switch to the Chrome extension.

2. **Why Modifying Binary / Ad-Hoc Re-signing Fails**:
   - Modern macOS applications enforce **Hardened Runtime**, **Apple App Attest (`DCAppAttestService`)**, and **Keychain Access Groups (`2DC432GLL2.com.openai.shared`)**.
   - Any binary modification and subsequent local ad-hoc re-signing (`codesign -s -`) strips the official OpenAI Team ID (`2DC432GLL2`), leading to:
     - Immediate loss of Keychain access (forcing logout).
     - Failure of Apple App Attest on OpenAI's login servers (`error_code: preauth_cookie_device_check_failed`).

3. **The Solution (Precision Selective Hook Architecture)**:
   - **Target Interception**: Only intercepts `https://ios.chat.openai.com/.../app_support_status/v1` and replies with `{"status":"supported"}`.
   - **Raw TCP Blind Tunneling**: Performs raw bidirectional TCP passthrough for `chatgpt.com`, `apple.com` (App Attest), and all regular websites. This preserves original Cloudflare/OpenAI SSL certificates with zero TLS decrypt errors (`net::ERR_CERT_AUTHORITY_INVALID`) and zero password prompts.
   - **Official Binary Preserved**: The app binary remains 100% untouched and signed with OpenAI's official Developer ID certificate.

---

## Project Structure

```
.
├── atlas_unblocker.py            # Core precision proxy daemon
├── com.openai.atlas.unblocker.plist # macOS launchd service configuration
├── install.sh                    # One-click installation script
├── uninstall.sh                  # One-click uninstallation script
└── README.md                     # Documentation
```

---

## Quick Start

### 1. Install & Enable

```bash
git clone https://github.com/fusiondrive/chatgpt-atlas-unblocker.git
cd chatgpt-atlas-unblocker
./install.sh
```

The daemon will be registered under macOS `launchd` as `com.openai.atlas.unblocker` and start automatically in the background on system boot.

### 2. Uninstall & Clean Up

```bash
./uninstall.sh
```

Restores system Wi-Fi proxy settings and removes the background service.

---

## Verification

To verify the mock endpoint directly:

```bash
curl -x 127.0.0.1:8989 -k -s "https://ios.chat.openai.com/public-api/mobile/app_support_status/v1"
# Returns: {"status":"supported","soft_deprecation":null,"hard_deprecation":null}
```
