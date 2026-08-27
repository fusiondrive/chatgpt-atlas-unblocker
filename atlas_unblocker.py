#!/usr/bin/env python3
"""
ChatGPT Atlas Sunset & Deprecation Unblocker
Author: Steve Wang (fusiondrive)

- Selectively intercepts ios.chat.openai.com sunset check endpoint (/public-api/mobile/app_support_status/v1)
  and returns status: supported.
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

DATA_DIR = os.path.expanduser("~/.chatgpt-atlas-unblocker")
CERT_FILE = os.path.join(DATA_DIR, "atlas_ios.crt")
KEY_FILE = os.path.join(DATA_DIR, "atlas_ios.key")
HOST = "127.0.0.1"
PORT = 8989

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
        
        # Add to user login Keychain once
        subprocess.run([
            "security", "add-trusted-cert", "-d", "-r", "trustRoot",
            "-k", os.path.expanduser("~/Library/Keychains/login.keychain-db"),
            CERT_FILE
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
        method, path, proto = req_line.split(" ", 2)

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

def enable_system_proxy():
    subprocess.run(["networksetup", "-setwebproxy", "Wi-Fi", HOST, str(PORT)], check=False)
    subprocess.run(["networksetup", "-setsecurewebproxy", "Wi-Fi", HOST, str(PORT)], check=False)
    subprocess.run(["networksetup", "-setwebproxystate", "Wi-Fi", "on"], check=False)
    subprocess.run(["networksetup", "-setsecurewebproxystate", "Wi-Fi", "on"], check=False)

def disable_system_proxy():
    subprocess.run(["networksetup", "-setwebproxystate", "Wi-Fi", "off"], check=False)
    subprocess.run(["networksetup", "-setsecurewebproxystate", "Wi-Fi", "off"], check=False)

def cleanup(sig=None, frame=None):
    disable_system_proxy()
    sys.exit(0)

def main():
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
