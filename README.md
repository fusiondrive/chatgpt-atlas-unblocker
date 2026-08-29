# ChatGPT Atlas Sunset & Deprecation Patcher

A zero-background-overhead, native binary patcher to eliminate the full-screen deprecation/sunset blocking modal in OpenAI's **ChatGPT Atlas** macOS application.

---

## Technical Mechanism

1. **The Sunset Check**:
   - When ChatGPT Atlas launches, `Aura.framework` invokes `ChatGPTSunset.SunsetStatus.init` to evaluate the sunset status.
   - When OpenAI returns `hard_deprecation`, the SwiftUI layer renders an unclosable full-screen card dialog (`BrowserSunsetDialogView`) blocking all interactions and prompting the user to switch to the Chrome extension.

2. **The Native Binary Patch Solution**:
   - Directly patches the assembly instructions of `ChatGPTSunset.SunsetStatus.init` in `Aura.framework` to always return `SunsetStatus.supported` (`mov x0, #2; ret`).
   - Completely eliminates the need for background proxy daemons, root CA certificates, TLS interception, and system network proxy modifications.
   - Re-signs the app locally with ad-hoc signing (`codesign -s -`) and hardware capability entitlements.
   - Normal ChatGPT clients (`ChatGPT.app` / `ChatGPT Classic.app`) and other applications are 100% untouched and unaffected.

---

## Quick Start

### 1. Patch & Enable

```bash
cd chatgpt-atlas-unblocker
./install.sh
```

### 2. Restore Original Binary

```bash
./uninstall.sh
```

---

## Frequently Asked Questions (FAQ)

### Why does Atlas ask to log in once after patching?
When an application binary is modified and re-signed locally, macOS Keychain Services isolates the Keychain items stored under OpenAI's official Apple Developer ID (`2DC432GLL2`). You only need to log in **once** via the web interface; the new session credentials will be saved and persisted normally for all subsequent launches.
