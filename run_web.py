"""Entry point for OScope Web Application.

Launches the OScope HTTP server and automatically opens the user's default browser.
"""

import argparse
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

# Ensure repo root and web are in sys.path
repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from web.server import run_server


def find_free_port(start_port: int = 8080, max_attempts: int = 10) -> int:
    """Find an open TCP port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start_port


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the OScope Web Simulation Laboratory.")
    parser.add_argument("--port", type=int, default=0, help="Port to listen on (default: auto-detect from 8080)")
    parser.add_argument("--bind", type=str, default="127.0.0.1", help="Address to bind to (default: 127.0.0.1)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open default web browser")
    args = parser.parse_args()

    port = args.port if args.port > 0 else find_free_port(8080)
    url = f"http://{args.bind}:{port}"

    if not args.no_browser:
        def open_browser():
            time.sleep(0.8)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    run_server(port=port, bind_address=args.bind)
    return 0


if __name__ == "__main__":
    sys.exit(main())
