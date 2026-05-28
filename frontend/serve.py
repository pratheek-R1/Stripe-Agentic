#!/usr/bin/env python3
"""
serve.py  -  Paygentic Frontend Development Server
====================================================
Serves the frontend static files AND proxies API requests to the
uAgents backend, eliminating all CORS issues.

Usage:
    python frontend/serve.py

Then open:
    http://localhost:3000

The backend (run_agents.py) must already be running on port 8000.
"""

import http.server
import urllib.request
import urllib.error
import json
import os
import sys
import socket

# Force UTF-8 console output on Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

# ── Config ───────────────────────────────────────────────────────────────────
FRONTEND_PORT = 3000
BACKEND_URL   = "http://localhost:8000"

FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths that should be proxied to the backend (POST)
PROXY_PATHS = {"/create_payment_nl", "/generate_payment_link"}

# Windows socket errors that mean the browser dropped the connection
_CONN_ERRORS = (
    BrokenPipeError,
    ConnectionAbortedError,   # WinError 10053
    ConnectionResetError,     # WinError 10054
)


class PaygenticHandler(http.server.SimpleHTTPRequestHandler):
    """Serves static files and proxies API POST requests to the backend."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    # ── CORS preflight ────────────────────────────────────────────────────────
    def do_OPTIONS(self):
        try:
            self.send_response(200)
            self._cors_headers()
            self.end_headers()
        except _CONN_ERRORS:
            pass

    # ── Proxy POST requests to backend ────────────────────────────────────────
    def do_POST(self):
        if self.path not in PROXY_PATHS:
            try:
                self.send_error(404, "Not found")
            except _CONN_ERRORS:
                pass
            return

        # Read request body
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
        except Exception as exc:
            print("[proxy] Failed to read request body:", exc)
            return

        target = BACKEND_URL + self.path
        print("[proxy] POST", self.path, "->", target)

        # Forward to backend
        req = urllib.request.Request(
            target,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        backend_data   = None
        status_code    = 502

        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                backend_data = resp.read()
                status_code  = resp.status
                print("[proxy] <- backend", status_code, "(%d bytes)" % len(backend_data))

        except urllib.error.HTTPError as exc:
            backend_data = exc.read()
            status_code  = exc.code
            print("[proxy] <- backend HTTP error", status_code)

        except Exception as exc:
            print("[proxy] Backend unreachable:", exc)
            backend_data = json.dumps({
                "status": "error",
                "details": "Backend error: " + str(exc),
                "payment_link": ""
            }).encode("utf-8")
            status_code = 502

        # Send response back to browser
        # Include Content-Length so the browser knows the exact payload size
        # and does not close the connection prematurely on Windows.
        self._send_response(status_code, backend_data)

    # ── Safe response writer ──────────────────────────────────────────────────
    def _send_response(self, status_code, data: bytes):
        """Write HTTP response with full error handling for dropped connections."""
        try:
            self.send_response(status_code)
            self._cors_headers()
            self.send_header("Content-Type",   "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection",     "close")
            self.end_headers()
        except _CONN_ERRORS as exc:
            print("[proxy] Connection dropped while sending headers:", type(exc).__name__)
            return
        except Exception as exc:
            print("[proxy] Header write error:", exc)
            return

        # Write body in chunks so a mid-write abort is caught cleanly
        try:
            self.wfile.write(data)
            self.wfile.flush()
            print("[proxy] Response sent OK (%d bytes)" % len(data))
        except _CONN_ERRORS as exc:
            # Browser closed the socket before we finished - this is benign.
            # The browser already received enough data to reconstruct the response
            # because we sent Content-Length, so the fetch() on the JS side
            # will still resolve correctly in most cases.
            print("[proxy] Connection closed by browser during body write (benign):", type(exc).__name__)
        except Exception as exc:
            print("[proxy] Unexpected write error:", type(exc).__name__, exc)

    # ── CORS headers helper ───────────────────────────────────────────────────
    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # ── Suppress noisy access logs (keep proxy logs only) ────────────────────
    def log_message(self, fmt, *args):
        msg = fmt % args
        # Only log non-static-file requests to keep output readable
        if any(p in msg for p in ['/create_payment', '/generate_payment', 'OPTIONS', '50', '40']):
            print("[serve]", self.address_string(), "-", msg)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.chdir(FRONTEND_DIR)

    # Use ThreadingHTTPServer to handle browser Keep-Alive connections concurrently.
    # A single-threaded HTTPServer will block on an idle connection,
    # causing subsequent fetch() requests to hang in 'pending'.
    server = http.server.ThreadingHTTPServer(("", FRONTEND_PORT), PaygenticHandler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    print("=" * 52)
    print("  Paygentic Frontend -> http://localhost:" + str(FRONTEND_PORT))
    print("  API proxy target   -> " + BACKEND_URL)
    print("=" * 52)
    print("  Make sure run_agents.py is running on port 8000")
    print("  Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[serve] Stopped.")
        server.server_close()
        sys.exit(0)
