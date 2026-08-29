#!/usr/bin/env python3
"""
ChatGPT Atlas Sunset Patcher
----------------------------
Bypasses the sunset deprecation takeover in ChatGPT Atlas macOS application
by directly patching the SunsetStatus initialization logic in Aura.framework.

No background proxies, no root certificates, no TLS MITM required.
"""

import os
import sys
import subprocess
import shutil

APP_PATH = "/Applications/ChatGPT Atlas.app"
AURA_PATH = os.path.join(APP_PATH, "Contents/Frameworks/Aura.framework/Versions/A/Aura")

ENTITLEMENTS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "https://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.device.audio-input</key>
    <true/>
    <key>com.apple.security.device.camera</key>
    <true/>
    <key>com.apple.security.personal-information.photos-library</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
</dict>
</plist>
"""

KNOWN_OFFSETS = {
    # Build 1.2026.189.1 (July 24, 2026)
    "1.2026.189.1": 0x2ddd630,
    # Build 1.2026.126.0 (May 29, 2026)
    "1.2026.126.0": 0x2b3d3c0,
}

PATCH_BYTES = bytes.fromhex("400080d2c0035fd6")  # mov x0, #2 (SunsetStatus.supported); ret

def get_app_version():
    info_plist = os.path.join(APP_PATH, "Contents/Info.plist")
    if not os.path.exists(info_plist):
        return None
    try:
        out = subprocess.check_output(["defaults", "read", info_plist, "CFBundleShortVersionString"])
        return out.decode("utf-8").strip()
    except Exception:
        return None

def patch_aura():
    if not os.path.exists(AURA_PATH):
        print(f"[-] Error: Aura framework binary not found at {AURA_PATH}")
        sys.exit(1)

    version = get_app_version()
    print(f"[+] Detected ChatGPT Atlas version: {version}")

    offset = KNOWN_OFFSETS.get(version)
    if not offset:
        print("[*] Searching binary for SunsetStatus.init signature...")
        with open(AURA_PATH, "rb") as f:
            data = f.read()
        for ver, off in KNOWN_OFFSETS.items():
            if off + 8 <= len(data):
                chunk = data[off:off+8]
                if chunk == PATCH_BYTES:
                    print(f"[+] Binary is already patched at offset {hex(off)}")
                    offset = off
                    break
                if chunk[:4] == bytes.fromhex("f44fbea9"):
                    offset = off
                    print(f"[+] Located SunsetStatus.init at {hex(offset)}")
                    break

    if not offset:
        print("[-] Could not automatically locate SunsetStatus.init offset for this build.")
        sys.exit(1)

    backup_path = AURA_PATH + ".original"
    if not os.path.exists(backup_path):
        print(f"[+] Creating backup at {backup_path}")
        shutil.copy2(AURA_PATH, backup_path)

    print(f"[+] Applying patch at offset {hex(offset)} -> mov x0, #2; ret")
    with open(AURA_PATH, "r+b") as f:
        f.seek(offset)
        f.write(PATCH_BYTES)

    entitlements_path = "/tmp/atlas_entitlements.plist"
    with open(entitlements_path, "w") as f:
        f.write(ENTITLEMENTS_XML)

    print("[+] Re-signing ChatGPT Atlas with ad-hoc signature...")
    subprocess.run([
        "codesign", "--force", "--deep", "-s", "-",
        "--entitlements", entitlements_path,
        APP_PATH
    ], check=True)

    if os.path.exists(entitlements_path):
        os.remove(entitlements_path)

    print("[+] Patch applied and verified successfully!")
    return True

if __name__ == "__main__":
    patch_aura()
