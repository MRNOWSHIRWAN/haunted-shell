import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from haunted_shell.backend import OllamaBackend


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers["Content-Length"])
        payload = json.loads(self.rfile.read(n))
        assert payload["model"] == "test-ghost"
        assert payload["messages"][0]["role"] == "system"
        body = json.dumps({
            "choices": [{"message": {"content": "  boo.  "}}]
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def test_ollama_backend_parses_reply():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/v1"
    b = OllamaBackend(base_url=url, model="test-ghost", timeout=5)
    assert b.whisper([{"role": "system", "content": "s"},
                      {"role": "user", "content": "u"}]) == "boo."
    server.shutdown()


def test_remote_endpoint_refused():
    import pytest
    with pytest.raises(SystemExit):
        OllamaBackend(base_url="https://api.example.com/v1")


def test_remote_endpoint_explicit_override():
    # documented escape hatch exists, but must be deliberate
    import os
    os.environ["HAUNT_ALLOW_REMOTE"] = "1"
    try:
        b = OllamaBackend(base_url="https://api.example.com/v1")
        assert b.base_url == "https://api.example.com/v1"
    finally:
        del os.environ["HAUNT_ALLOW_REMOTE"]


def test_redirect_not_followed():
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Redirector(BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(302)
            self.send_header("Location", "https://evil.example.com/collect")
            self.end_headers()

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 0), Redirector)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/v1"
    b = OllamaBackend(base_url=url, timeout=5)
    import pytest
    with pytest.raises(Exception):
        b.whisper([{"role": "user", "content": "x"}])
    server.shutdown()
