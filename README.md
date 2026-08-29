# ChatGPT Atlas Sunset & Deprecation Unblocker

A lightweight, zero-side-effect network hook daemon to eliminate the full-screen deprecation/sunset blocking modal in OpenAI's **ChatGPT Atlas** macOS application while preserving 100% official Apple Developer ID code signatures, Apple App Attest / DeviceCheck hardware verification, and Keychain session persistence.

---

## Background & Technical Root Cause

1. **The Sunset Mechanism**:
   - When ChatGPT Atlas launches, its internal `Aura.framework` queries:
     `GET https://ios.chat.openai.com/public-api/mobile/app_support_status/v1`
   - When OpenAI returns `{"status": "hard_deprecation"}`, the SwiftUI layer renders an unclosable full-screen card dialog (`BrowserSunsetDialogView`) blocking all interactions and prompting the user to switch to the Chrome extension.

2. **Why Simple Self-Signed Certs Fail (SSL Pinning)**:
   - `Aura.framework` contains built-in SSL Public Key Pinning (`APIClient/CertificatePinning.swift`).
   - If an intercepting proxy presents a self-signed certificate, even if trusted in macOS Keychain, `SecTrustEvaluate` fails the public key hash verification and displays:
     > *"Looks like 'ios.chat.openai.com' is the wrong SSL certificate — this could mean someone is tampering with your device or network."*
   - **The Fix**: OpenAI's `APIClient` checks `CFPreferencesCopyAppValue(CFSTR("com.openai.pinned_cert_hash_list"), ...)` in `UserDefaults`. Our unblocker dynamically computes the SHA256 public key hash of the local certificate and registers it alongside official OpenAI root keys, achieving 100% clean verification pass.

3. **Why Modifying Binary / Ad-Hoc Re-signing Fails**:
   - Modern macOS applications enforce **Hardened Runtime**, **Apple App Attest (`DCAppAttestService`)**, and **Keychain Access Groups (`2DC432GLL2.com.openai.shared`)**.
   - Any binary modification and subsequent local ad-hoc re-signing (`codesign -s -`) strips the official OpenAI Team ID (`2DC432GLL2`), leading to:
     - Immediate loss of Keychain access (forcing logout).
     - Failure of Apple App Attest on OpenAI's login servers (`error_code: preauth_cookie_device_check_failed`).
     - Process spawn rejection on macOS Sequoia/Sonoma (`amfid: Adhoc signed app with restricted entitlements detected`).

4. **The Solution (Precision Selective Hook Architecture)**:
   - **Target Interception**: Only intercepts `https://ios.chat.openai.com/.../app_support_status/v1` and replies with `{"status":"supported"}`.
   - **Native SSL Pinning Bypass**: Dynamically injects local CA public key hash into `com.openai.pinned_cert_hash_list`.
   - **Raw TCP Blind Tunneling**: Performs raw bidirectional TCP passthrough for `chatgpt.com`, `apple.com` (App Attest), and all regular websites. This preserves original Cloudflare/OpenAI SSL certificates with zero TLS decrypt errors (`net::ERR_CERT_AUTHORITY_INVALID`) and zero password prompts.
   - **Official Binary Preserved**: The app binary remains 100% untouched and signed with OpenAI's official Developer ID certificate.

---

## Project Structure

```
.
├── atlas_unblocker.py            # Core precision proxy daemon & pinning manager
├── com.openai.atlas.unblocker.plist # macOS launchd service configuration
├── install.sh                    # One-click installation script
├── uninstall.sh                  # One-click uninstallation script
└── README.md                     # Documentation
```

---

## Quick Start

### 1. Install & Enable

```bash
cd chatgpt-atlas-unblocker
./install.sh
```

The daemon will be registered under macOS `launchd` as `com.openai.atlas.unblocker` and start automatically in the background on system boot.

### 2. Uninstall & Clean Up

```bash
./uninstall.sh
```

Restores system proxy settings, removes Keychain certificates, cleans up UserDefaults, and removes the background service.

---

## Verification

To verify the mock endpoint directly:

```bash
curl -x 127.0.0.1:8989 -k -s "https://ios.chat.openai.com/public-api/mobile/app_support_status/v1"
# Returns: {"status":"supported","soft_deprecation":null,"hard_deprecation":null}
```
