import os
import subprocess
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "docker/tunnel/start.sh"

class TunnelInputTests(unittest.TestCase):
    def reject(self, **overrides):
        env = dict(os.environ, VAST_SSH_HOST="gpu.example.com", VAST_SSH_PORT="2222", VAST_SSH_USER="root")
        env.update(overrides)
        result = subprocess.run(["sh", str(SCRIPT)], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)

    def test_host_cannot_be_an_ssh_option(self):
        self.reject(VAST_SSH_HOST="-oProxyCommand=sh")

    def test_user_cannot_be_an_ssh_option(self):
        self.reject(VAST_SSH_USER="-v")

    def test_host_cannot_inject_shell_syntax(self):
        self.reject(VAST_SSH_HOST="host;touch /tmp/unwanted")

    def test_port_must_be_in_range(self):
        for port in ("0", "65536", "22 -oStrictHostKeyChecking=no"):
            with self.subTest(port=port):
                self.reject(VAST_SSH_PORT=port)
