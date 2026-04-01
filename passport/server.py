"""HTTP server for exposing agent passport over the network."""

import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from .card import AgentCard
from .verifier import verify_card


class PassportRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for passport server."""

    passport_path: str = ""
    passport_data: Optional[Dict[str, Any]] = None

    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"[{self.log_date_time_string()}] {format % args}")

    def send_json_response(self, data: Dict[str, Any], status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode("utf-8"))

    def send_error_response(self, message: str, status: int = 400):
        """Send error response."""
        self.send_json_response({"error": message}, status=status)

    def do_GET(self):
        """Handle GET requests."""
        path = urlparse(self.path).path

        if path == "/health":
            self.handle_health()
        elif path == "/passport":
            self.handle_get_passport()
        elif path == "/verify":
            self.handle_verify()
        else:
            self.send_error_response("Not found", status=404)

    def do_POST(self):
        """Handle POST requests."""
        path = urlparse(self.path).path

        if path == "/exchange":
            self.handle_exchange()
        else:
            self.send_error_response("Not found", status=404)

    def handle_health(self):
        """Handle /health endpoint."""
        if not self.passport_data:
            self.send_json_response(
                {"status": "ok", "agent": "unknown", "message": "No passport loaded"},
                status=200,
            )
            return

        agent_name = self.passport_data.get("name", "unknown")
        self.send_json_response({"status": "ok", "agent": agent_name})

    def handle_get_passport(self):
        """Handle /passport endpoint."""
        if not self.passport_data:
            self.send_error_response("No passport loaded", status=500)
            return

        self.send_json_response(self.passport_data)

    def handle_verify(self):
        """Handle /verify endpoint."""
        if not self.passport_data:
            self.send_error_response("No passport loaded", status=500)
            return

        signature = self.passport_data.get("signature")
        if not signature:
            self.send_json_response(
                {
                    "valid": False,
                    "signed": False,
                    "message": "Passport is not signed",
                }
            )
            return

        # Note: Full verification requires public key, so we just confirm it's signed
        self.send_json_response(
            {
                "valid": True,
                "signed": True,
                "agent_id": self.passport_data.get("agent_id"),
                "name": self.passport_data.get("name"),
                "message": "Passport is signed (full verification requires public key)",
            }
        )

    def handle_exchange(self):
        """Handle /exchange endpoint - receive remote passport, send ours."""
        # Read incoming passport
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self.send_error_response("No data received")
            return

        try:
            body = self.rfile.read(content_length)
            incoming_passport = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_error_response("Invalid JSON")
            return

        # Validate incoming passport has required fields
        required_fields = ["agent_id", "name"]
        for field in required_fields:
            if field not in incoming_passport:
                self.send_error_response(f"Missing required field: {field}")
                return

        # Log the exchange
        remote_agent = incoming_passport.get("name", "unknown")
        remote_id = incoming_passport.get("agent_id", "unknown")
        print(f"Exchange request from: {remote_agent} ({remote_id})")

        # Return our passport
        if not self.passport_data:
            self.send_error_response("No passport loaded", status=500)
            return

        self.send_json_response(self.passport_data)


def load_passport(passport_path: str) -> Dict[str, Any]:
    """Load passport from file.

    Args:
        passport_path: Path to passport JSON file

    Returns:
        Passport data as dictionary

    Raises:
        FileNotFoundError: If passport file doesn't exist
        json.JSONDecodeError: If passport is invalid JSON
    """
    if not os.path.exists(passport_path):
        raise FileNotFoundError(f"Passport not found: {passport_path}")

    with open(passport_path, "r") as f:
        return json.load(f)


def serve_passport(
    passport_path: Optional[str] = None,
    port: int = 8500,
    host: str = "0.0.0.0",
):
    """Start HTTP server to serve passport.

    Args:
        passport_path: Path to passport file (default: ~/.ai-iq-passport/passport.json)
        port: Port to listen on (default: 8500)
        host: Host to bind to (default: 0.0.0.0)
    """
    # Determine passport path
    if not passport_path:
        passport_path = str(Path.home() / ".ai-iq-passport" / "passport.json")

    # Load passport
    try:
        passport_data = load_passport(passport_path)
    except Exception as e:
        print(f"Error loading passport: {e}")
        return 1

    # Set class variables for handler
    PassportRequestHandler.passport_path = passport_path
    PassportRequestHandler.passport_data = passport_data

    # Start server
    server_address = (host, port)
    httpd = HTTPServer(server_address, PassportRequestHandler)

    agent_name = passport_data.get("name", "unknown")
    print(f"Serving passport for: {agent_name}")
    print(f"Server running at: http://{host}:{port}")
    print(f"Endpoints:")
    print(f"  GET  /health   - Server health check")
    print(f"  GET  /passport - Get full passport")
    print(f"  GET  /verify   - Check signature status")
    print(f"  POST /exchange - Exchange passports")
    print(f"\nPress Ctrl+C to stop")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
        return 0

    return 0
