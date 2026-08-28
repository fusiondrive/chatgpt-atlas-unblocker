# ChatGPT Atlas Sunset Patcher

A clean, native binary patcher for OpenAI's **ChatGPT Atlas** macOS application to permanently bypass the sunset deprecation modal while preserving 100% native TLS connections, Apple Keychain access groups, and official API functionality.

---

## Technical Overview

### 1. Root Cause of Sunset Blocking
Upon startup, ChatGPT Atlas evaluates the app support status returned by OpenAI's mobile support endpoint:
`GET https://ios.chat.openai.com/public-api/mobile/app_support_status/v1`

When the response contains `{"status": "hard_deprecation"}`, `Aura.framework` invokes `ChatGPTSunset.SunsetStatus.init(rawValue:)` and triggers an unclosable full-screen deprecation dialog (`BrowserSunsetDialogView`).

### 2. Why TLS Proxies & MITM Are Problematic
- Intercepting `ios.chat.openai.com` with a local self-signed TLS certificate triggers Chromium / WebKit SSL certificate pinning checks (`error: ios.chat.openai.com is the wrong SSL certificate`).
- This SSL error breaks token exchange and conversation stream requests, causing SideChat and Ask GPT responses to fail.

### 3. The Clean Solution: Native Binary Hook + Entitlements
This patcher performs a surgical, non-invasive patch directly inside `Aura.framework`:
- **Function Hook**: Overwrites `ChatGPTSunset.SunsetStatus.init(rawValue:)` to always return `SunsetStatus.supported` (`mov x0, #2; ret`).
- **Zero TLS MITM**: All network traffic goes directly over genuine, official HTTPS to OpenAI's servers with zero certificate tampering.
- **Keychain Entitlements Preserved**: Application is re-signed with the official `keychain-access-groups` (`2DC432GLL2.com.openai.shared`) and application group identifiers, preserving login persistence and preventing `preauth_cookie_device_check_failed` errors.

---

## Supported Versions

| Version | Build Date | Patch Offset | Status |
| :--- | :--- | :--- | :--- |
| **`1.2026.189.1`** (Latest) | 2026-07-24 | `0x2ddd630` | Supported |
| **`1.2026.126.0`** | 2026-05-29 | `0x2b3d3c0` | Supported |

---

## Quick Start

### 1. Run the Patcher

```bash
git clone https://github.com/fusiondrive/chatgpt-atlas-unblocker.git
cd chatgpt-atlas-unblocker
./install.sh
```

### 2. Launch ChatGPT Atlas

Open `/Applications/ChatGPT Atlas.app` normally. The app will launch straight into the browser interface without any sunset dialog or proxy requirements.

---

## Uninstall / Restore

To revert the application to its original unmodified binary:

```bash
./uninstall.sh
```

---

## License

MIT License. For educational and research purposes only.
