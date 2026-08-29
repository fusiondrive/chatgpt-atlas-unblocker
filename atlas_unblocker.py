#!/usr/bin/env python3
"""
ChatGPT Atlas Sunset & Deprecation Unblocker
Author: Steve Wang (fusiondrive)

- Selectively intercepts ios.chat.openai.com sunset check endpoint (/public-api/mobile/app_support_status/v1)
  and returns status: supported.
- Eliminates "Wrong SSL certificate / Certificate Pinning" errors by dynamically registering the local CA public key
  hash into OpenAI's Aura framework preference store (com.openai.pinned_cert_hash_list).
- Performs 100% raw TCP blind tunneling for chatgpt.com, apple.com (App Attest), and all other domains.
- Preserves 100% official Apple Developer ID code signature, Keychain access groups, and login state.
"""

import os
import sys
import socket
import select
import ssl
import threading
import subprocess
import signal
import hashlib
import base64

DATA_DIR = os.path.expanduser("~/.chatgpt-atlas-unblocker")
CERT_FILE = os.path.join(DATA_DIR, "atlas_ios.crt")
KEY_FILE = os.path.join(DATA_DIR, "atlas_ios.key")
HOST = "127.0.0.1"
PORT = 8989

OPENAI_DEFAULT_PINNED_HASHES = [
    "C5+lpZ7tcVwmwQIMcRtPbsQtWLABXhQzejna0wHFr8M=",
    "diGVwiVYbubAI3RW4hB9xU8e/CH2GnkuvVFZE8zmgzI=",
    "x+C0kJ2uYxDLS5lLqDkAFQRmwWLeak0Kk1WsiuDRnZ4=",
    "Y9mvm0exBk1JoQ57f9Vm28jKo5lFm/woKcVxrYxu80o=",
    "r/mIkG3eEpVdm+u/ko/cwxzOMo1bk4TyHIlByibiA5E=",
    "i7WTqTvh0OioIruIfFR4kMPnBqrS2rdiVPl/s2uC/CY=",
    "uUwZgwDOxcBXrQcntwu+kYFpkiVkOaezL0WYEZ3anJc=",
    "NfU84SZGEeAzQP434ex9TMmGxWE9ynD9BKpEVF8tryg=",
    "svcpi1K/LDysTd/nLeTWgqxYlXWVmC8rYjAa9ZfGmcU=",
    "I/Lt/z7ekCWanjD0Cvj5EqXls2lOaThEA0H2Bg4BT/o=",
    "8ca6Zwz8iOTfUpc8rkIPCgid1HQUT+WAbEIAZOFZEik=",
    "Fe7TOVlLME+M+Ee0dzcdjW/sYfTbKwGvWJ58U7Ncrkw=",
    "WoiWRyIOVNa9ihaBciRSC7XHjliYS9VwUGOIud4PB18=",
    "Wd8xe/qfTwq3ylFNd3IpaqLHZbh2ZNCLluVzmeNkcpw=",
    "K87oWBWM9UZfyddvDfoxL+8lpNyoUB2ptGtn0fv6G2Q=",
    "cGuxAXyFXFkWm61cF4HPWX8S0srS9j0aSqN0k4AP+4A=",
    "fg6tdrtoGdwvVFEahDVPboswe53YIFjqbABPAdndpd8=",
    "aCdH+LpiG4fN07wpXtXKvOciocDANj0daLOJKNJ4fx4=",
    "Ko8tivDrEjiY90yGasP6ZpBU4jwXvHqVvQI0GS3GNdA=",
    "gI1os/q0iEpflxrOfRBVDXqVoWN3Tz7Dav/7IT++THQ=",
    "AG1751Vd2CAmRCxPGieoDomhmJy4ezREjtIZTBgZbV4=",
    "58qRu/uxh4gFezqAcERupSkRYBlBAvfcw7mEjGPLnNU=",
    "grX4Ta9HpZx6tSHkmCrvpApTQGo67CYDnvprLg5yRME=",
    "ICGRfpgmOUXIWcQ/HXPLQTkFPEFPoDyjvH7ohhQpjzs=",
    "x4QzPSC810K5/cMjb05Qm4k3Bw5zBn4lTdO/nEW/Td4=",
    "hxqRlPTu1bMS/0DITB1SSu0vd4u/8l8TjPgfaAp63Gc=",
    "Vfd95BwDeSQo+NUYxVEEIlvkOlWY2SalKK1lPhzOx78=",
    "QXnt2YHvdHR3tJYmQIr0Paosp6t/nggsEGD4QJZ3Q0g=",
    "mEflZT5enoR1FuXLgYYGqnVEoZvmf9c2bVBpiOjYQ0c=",
]

def compute_cert_pin_hash(cert_path):
    """
    Computes the SHA256 base64 hash of the PKCS#1 RSA Public Key,
    matching macOS SecKeyCopyExternalRepresentation + CC_SHA256 used in Aura.framework.
    """
    try:
        spki_der = subprocess.check_output(
            ["openssl", "x509", "-in", cert_path, "-pubkey", "-noout"],
            stderr=subprocess.DEVNULL
        )
        rsa_pkcs1 = subprocess.check_output(
            ["openssl", "rsa", "-pubin", "-RSAPublicKey_out", "-outform", "DER"],
            input=spki_der,
            stderr=subprocess.DEVNULL
        )
        return base64.b64encode(hashlib.sha256(rsa_pkcs1).digest()).decode()
    except Exception:
        return None

def update_pinned_hashes(local_hash):
    """
    Injects the local certificate hash into macOS UserDefaults for OpenAI apps.
    Aura's CertificatePinning checks CFPreferencesCopyAppValue("com.openai.pinned_cert_hash_list").
    """
    if not local_hash:
        return
    all_hashes = [local_hash] + [h for h in OPENAI_DEFAULT_PINNED_HASHES if h != local_hash]
    target_domains = ["com.openai.atlas", "com.openai.chat", "com.openai.codex"]
    for domain in target_domains:
        try:
            cmd = ["defaults", "write", domain, "com.openai.pinned_cert_hash_list", "-array"] + all_hashes
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def ensure_ca():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not (os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE)):
        cmd = [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", KEY_FILE, "-out", CERT_FILE,
            "-days", "3650", "-nodes",
            "-subj", "/CN=ios.chat.openai.com",
            "-addext", "subjectAltName=DNS:ios.chat.openai.com"
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Add to user login Keychain
        subprocess.run([
            "security", "add-trusted-cert", "-d", "-r", "trustRoot",
            "-k", os.path.expanduser("~/Library/Keychains/login.keychain-db"),
            CERT_FILE
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Compute and register pinned certificate public key hash into UserDefaults
    local_hash = compute_cert_pin_hash(CERT_FILE)
    if local_hash:
        update_pinned_hashes(local_hash)

def tunnel_sockets(s1, s2):
    try:
        while True:
            r, _, _ = select.select([s1, s2], [], [], 60)
            if not r:
                break
            if s1 in r:
                data = s1.recv(16384)
                if not data:
                    break
                s2.sendall(data)
            if s2 in r:
                data = s2.recv(16384)
                if not data:
                    break
                s1.sendall(data)
    except Exception:
        pass
    finally:
        try: s1.close()
        except: pass
        try: s2.close()
        except: pass

def handle_tls_intercept(client_sock, target_host, target_port):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT_FILE, keyfile=KEY_FILE)
    
    try:
        tls_client = context.wrap_socket(client_sock, server_side=True)
    except Exception:
        client_sock.close()
        return

    try:
        req_data = b""
        while b"\r\n\r\n" not in req_data:
            chunk = tls_client.recv(4096)
            if not chunk:
                break
            req_data += chunk

        if not req_data:
            tls_client.close()
            return

        header_part = req_data.split(b"\r\n\r\n")[0].decode('latin-1')
        lines = header_part.split("\r\n")
        req_line = lines[0]
        parts = req_line.split(" ", 2)
        path = parts[1] if len(parts) > 1 else ""

        # Check if sunset status check
        if "app_support_status" in path:
            body = b'{"status":"supported","soft_deprecation":null,"hard_deprecation":null}'
            resp = (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: application/json\r\n"
                b"Access-Control-Allow-Origin: *\r\n"
                b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                b"Connection: close\r\n\r\n" + body
            )
            tls_client.sendall(resp)
            tls_client.close()
            return

        # Forward other ios.chat.openai.com requests
        upstream_ctx = ssl.create_default_context()
        upstream_sock = socket.create_connection((target_host, target_port), timeout=15)
        tls_upstream = upstream_ctx.wrap_socket(upstream_sock, server_hostname=target_host)
        tls_upstream.sendall(req_data)
        tunnel_sockets(tls_client, tls_upstream)
    except Exception:
        try: tls_client.close()
        except: pass

def handle_client(client_sock):
    try:
        req = client_sock.recv(4096)
        if not req:
            client_sock.close()
            return

        lines = req.split(b"\r\n")
        req_line = lines[0].decode('latin-1')
        parts = req_line.split(" ")
        method = parts[0]

        if method == "CONNECT":
            dest = parts[1]
            if ":" in dest:
                target_host, target_port = dest.split(":", 1)
                target_port = int(target_port)
            else:
                target_host = dest
                target_port = 443

            client_sock.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")

            # ONLY intercept ios.chat.openai.com
            if target_host == "ios.chat.openai.com":
                handle_tls_intercept(client_sock, target_host, target_port)
            else:
                # 100% RAW TCP tunnel for chatgpt.com, apple.com, google.com, etc.
                upstream = socket.create_connection((target_host, target_port), timeout=15)
                tunnel_sockets(client_sock, upstream)
        else:
            client_sock.close()
    except Exception:
        try: client_sock.close()
        except: pass

def get_network_services():
    try:
        out = subprocess.check_output(
            ["networksetup", "-listallnetworkservices"],
            stderr=subprocess.DEVNULL
        ).decode().splitlines()
        services = []
        for line in out:
            line = line.strip()
            if not line or "asterisk" in line.lower():
                continue
            services.append(line)
        return services if services else ["Wi-Fi", "Ethernet"]
    except Exception:
        return ["Wi-Fi", "Ethernet"]

def enable_system_proxy():
    for service in get_network_services():
        subprocess.run(["networksetup", "-setwebproxy", service, HOST, str(PORT)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["networksetup", "-setsecurewebproxy", service, HOST, str(PORT)], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["networksetup", "-setwebproxystate", service, "on"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["networksetup", "-setsecurewebproxystate", service, "on"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def disable_system_proxy():
    for service in get_network_services():
        subprocess.run(["networksetup", "-setwebproxystate", service, "off"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["networksetup", "-setsecurewebproxystate", service, "off"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def cleanup(sig=None, frame=None):
    disable_system_proxy()
    sys.exit(0)

def main():
    if "--setup-only" in sys.argv:
        ensure_ca()
        enable_system_proxy()
        print("[+] Setup completed.")
        return

    ensure_ca()
    enable_system_proxy()

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(128)

    try:
        while True:
            client, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(client,), daemon=True)
            t.start()
    except KeyboardInterrupt:
        cleanup()

if __name__ == '__main__':
    main()
