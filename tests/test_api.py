import json
import threading
import urllib.request

from server import (
    HOST,
    AIBridgeHTTPRequestHandler,
    QuietThreadingTCPServer,
    create_directories,
)


def test_status_endpoint_returns_health_info():
    """The /api/status endpoint should return JSON with server status."""
    create_directories()
    httpd = QuietThreadingTCPServer((HOST, 0), AIBridgeHTTPRequestHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    try:
        url = f"http://{HOST}:{port}/api/status"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode())
        assert data["instance"] == "claude-a"
        assert "session_active" in data
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()
