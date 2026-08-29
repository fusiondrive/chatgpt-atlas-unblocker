# ChatGPT Atlas Sunset & Deprecation Unblocker

A lightweight, zero-side-effect network hook daemon to eliminate the full-screen deprecation/sunset blocking modal in OpenAI's **ChatGPT Atlas** macOS application while preserving 100% official Apple Developer ID code signatures, Apple App Attest / DeviceCheck hardware verification, and Keychain session persistence.

---

## Background & Technical Root Cause

1. **The Sunset Mechanism**:
   - When ChatGPT Atlas launches, its internal `Aura.framework` queries:
     `GET https://ios.chat.openai.com/public-api/mobile/app_support_status/v1`
   - When OpenAI returns `{"status": "hard_deprecation"}`, the SwiftUI layer renders an unclosable full-screen card dialog (`BrowserSunsetDialogView`) blocking all interactions and prompting the user to switch to the Chrome extension.

2. **Why Modifying Binary / Ad-Hoc Re-signing Fails**:
   - Modern macOS applications enforce **Apple App Attest (`DCAppAttestService`)** and **Keychain Access Groups (`2DC432GLL2.com.openai.shared`)**.
   - Any binary modification and local ad-hoc re-signing (`codesign -s -`) strips OpenAI's official Team ID (`2DC432GLL2`), causing OpenAI's login servers to reject device verification with `error_code: preauth_cookie_device_check_failed`.

3. **The Solution (Dynamic SSL Pinning Bypass & Precision Hook)**:
   - **Target Interception**: Only intercepts `https://ios.chat.openai.com/.../app_support_status/v1` and replies with `{"status":"supported"}`.
   - **Native SSL Pinning Bypass**: Dynamically injects local CA public key hash into `com.openai.pinned_cert_hash_list` in `UserDefaults`.
   - **Raw TCP Blind Tunneling**: Performs raw bidirectional TCP passthrough for `chatgpt.com`, `apple.com` (App Attest), and all regular websites.
   - **Official Binary Preserved**: The app binary remains 100% untouched and signed with OpenAI's official Developer ID certificate.

---

## Quick Start

### 1. Install & Enable

```bash
cd chatgpt-atlas-unblocker
./install.sh
```

### 2. Uninstall & Clean Up

```bash
./uninstall.sh
```
