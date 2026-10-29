"""OScope HTTP Application Server.

A robust multi-threaded HTTP server built on Python standard library
that serves the OScope modern web frontend and routes REST API requests
directly to the C++ simulation engine.
"""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import sys
from typing import Any, Dict
from urllib.parse import urlparse

# Ensure repository root and gui are on sys.path
web_dir = Path(__file__).resolve().parent
repo_root = web_dir.parent
gui_dir = repo_root / "gui"
for p in (str(repo_root), str(gui_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from web.api import OScopeApiHandler

# MIME types
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("image/svg+xml", ".svg")
mimetypes.add_type("application/json", ".json")


class OScopeRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler serving static SPA assets and JSON API endpoints."""

    api_handler: OScopeApiHandler = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(web_dir), **kwargs)

    def _send_json(self, data: Any, status: int = 200) -> None:
        """Helper to send JSON response with proper headers."""
        payload = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(payload)

    def _read_json_body(self) -> Dict[str, Any]:
        """Read and parse incoming JSON payload."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(body)
        except Exception as e:
            raise ValueError(f"Malformed JSON body: {e}")

    def do_OPTIONS(self) -> None:
        """Handle CORS pre-flight requests."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        """Route GET requests: APIs or SPA static files."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/status":
            try:
                status = self.api_handler.get_status()
                self._send_json(status)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        elif path == "/api/host-monitor/run":
            try:
                result = self.api_handler.run_host_monitor()
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        # Serve SPA: fallback root or unknown paths to index.html
        if path == "" or path == "/" or not (web_dir / path.lstrip("/")).exists():
            index_path = web_dir / "index.html"
            if index_path.exists():
                self.path = "/index.html"

        super().do_GET()

    def do_POST(self) -> None:
        """Route POST requests to simulation handlers."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            body = self._read_json_body()
        except Exception as e:
            self._send_json({"error": str(e)}, status=400)
            return

        try:
            if path == "/api/scheduling/run":
                res = self.api_handler.run_scheduling(body)
            elif path == "/api/memory/run":
                res = self.api_handler.run_memory(body)
            elif path == "/api/paging/run":
                res = self.api_handler.run_paging(body)
            elif path == "/api/deadlock/run":
                res = self.api_handler.run_deadlock(body)
            elif path == "/api/disk/run":
                res = self.api_handler.run_disk(body)
            elif path == "/api/linux/run":
                res = self.api_handler.run_linux(body)
            elif path == "/api/filesystem/run":
                res = self.api_handler.run_filesystem(body)
            elif path == "/api/address-translation/run":
                res = self.api_handler.run_address_translation(body)
            elif path == "/api/process-lifecycle/run":
                res = self.api_handler.run_process_lifecycle(body)
            else:
                self._send_json({"error": f"Endpoint not found: {path}"}, status=404)
                return

            self._send_json(res)
        except ValueError as ve:
            self._send_json({"error": str(ve), "type": "ValidationError"}, status=400)
        except Exception as e:
            self._send_json({"error": str(e), "type": "ExecutionError"}, status=500)

    def log_message(self, format, *args):
        """Clean custom server logging without spamming stderr."""
        sys.stdout.write(f"[{self.log_date_time_string()}] {format % args}\n")
        sys.stdout.flush()


def run_server(port: int = 8080, bind_address: str = "127.0.0.1") -> None:
    """Start the OScope Threading HTTP Server."""
    handler_instance = OScopeApiHandler()
    OScopeRequestHandler.api_handler = handler_instance

    server = ThreadingHTTPServer((bind_address, port), OScopeRequestHandler)
    print(f"\n=======================================================")
    print(f"  OScope Web Laboratory is running at:")
    print(f"  http://{bind_address}:{port}")
    print(f"=======================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down OScope Web Server...")
        server.server_close()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=port)
