"""Exercise the actual nginx policy against an isolated fake inference server."""
import http.server
import json
import os
import socket
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "test_" + "a" * 40

class Backend(http.server.BaseHTTPRequestHandler):
    seen = []
    def log_message(self, *args):
        pass
    def answer(self):
        Backend.seen.append((self.path, dict(self.headers)))
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length)) if length else {}
        if body.get("force_failure"):
            self.send_response(502)
            self.end_headers()
            return
        if self.path == "/v1/chat/completions":
            payload = b'data: {"choices":[{"delta":{"content":"ready"}}]}\n\ndata: [DONE]\n\n'
            kind = "text/event-stream"
        elif self.path == "/v1/models":
            payload = b'{"data":[{"id":"tpe-code:latest"}]}'
            kind = "application/json"
        else:
            payload = b'{"model":"tpe-code:latest"}'
            kind = "application/json"
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    do_GET = answer
    do_POST = answer

@unittest.skipUnless(os.environ.get("NGINX_BINARY"), "Set NGINX_BINARY to run real nginx policy tests")
class GatewayPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name)
        (cls.path / "logs").mkdir()
        cls.backend = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Backend)
        cls.thread = threading.Thread(target=cls.backend.serve_forever, daemon=True)
        cls.thread.start()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        config = (ROOT / "docker/gateway/nginx.conf").read_text()
        config = config.replace("worker_processes auto;", "worker_processes 1;")
        config = config.replace("include /etc/nginx/mime.types;", "")
        config = config.replace("/tmp/", str(cls.path) + "/")
        config = config.replace("listen 8080;", f"listen 127.0.0.1:{cls.port};")
        config = config.replace("/run/secrets/gateway_tokens.conf", str(cls.path / "tokens.conf"))
        config = config.replace("/etc/nginx/ai-proxy.conf", str(cls.path / "proxy.conf"))
        config = config.replace("127.0.0.1:11434", f"127.0.0.1:{cls.backend.server_port}")
        (cls.path / "nginx.conf").write_text(config)
        (cls.path / "tokens.conf").write_text(f'"Bearer {TOKEN}" development;\n')
        (cls.path / "proxy.conf").write_text((ROOT / "docker/gateway/proxy.conf").read_text())
        cls.process = subprocess.Popen(
            [os.environ["NGINX_BINARY"], "-p", str(cls.path), "-c", str(cls.path / "nginx.conf"), "-g", "daemon off;"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        for _ in range(100):
            if cls.process.poll() is not None:
                raise RuntimeError(cls.process.stderr.read().decode())
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{cls.port}/healthz", timeout=.2):
                    return
            except OSError:
                time.sleep(.02)
        raise RuntimeError("nginx did not start")

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.communicate(timeout=5)
        cls.backend.shutdown()
        cls.backend.server_close()
        cls.thread.join(timeout=5)
        cls.temp.cleanup()

    def request(self, path, token=TOKEN, payload=None, extra=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        headers.update(extra or {})
        data = json.dumps(payload).encode() if payload is not None else None
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}" + path, data=data, headers=headers)
        return urllib.request.urlopen(request, timeout=5)

    def test_missing_and_wrong_tokens_are_rejected_before_the_backend(self):
        before = len(Backend.seen)
        for token in (None, "wrong"):
            with self.subTest(token=token), self.assertRaises(urllib.error.HTTPError) as error:
                self.request("/v1/models", token=token)
            self.assertEqual(error.exception.code, 401)
        self.assertEqual(len(Backend.seen), before)

    def test_management_api_is_not_exposed_even_to_authenticated_callers(self):
        before = len(Backend.seen)
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/api/pull", payload={"model": "anything"})
        self.assertEqual(error.exception.code, 404)
        self.assertEqual(len(Backend.seen), before)

    def test_upstream_does_not_receive_gateway_credentials(self):
        with self.request("/v1/models", extra={"X-Api-Key": "must-not-leave-gateway"}) as response:
            self.assertEqual(json.load(response)["data"][0]["id"], "tpe-code:latest")
        headers = {k.lower(): v for k, v in Backend.seen[-1][1].items()}
        self.assertNotIn("authorization", headers)
        self.assertNotIn("x-api-key", headers)

    def test_streaming_is_preserved(self):
        with self.request("/v1/chat/completions", payload={"stream": True}) as response:
            self.assertEqual(response.headers["Content-Type"], "text/event-stream")
            payload = response.read()
            self.assertIn(b'"content":"ready"', payload)
            self.assertIn(b"data: [DONE]", payload)

    def test_backend_failure_becomes_service_unavailable(self):
        with self.assertRaises(urllib.error.HTTPError) as error:
            self.request("/v1/chat/completions", payload={"force_failure": True})
        self.assertEqual(error.exception.code, 503)
        self.assertIn(b"service_unavailable", error.exception.read())

    def test_ready_check_uses_the_expected_model(self):
        with self.request("/readyz") as response:
            self.assertEqual(response.status, 200)
        self.assertEqual(Backend.seen[-1][0], "/api/show")
