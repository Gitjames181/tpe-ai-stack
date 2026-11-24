"""Verify Komodo-supplied credentials fail closed and stay out of child envs."""
import base64
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class StartupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.run = self.root / "run"
        self.child = self.root / "child.json"
        self.env = dict(os.environ, AI_RUN_DIR=str(self.run), CHILD_RECORD=str(self.child),
                        PATH=str(self.bin) + os.pathsep + os.environ["PATH"])
        for name in ("ssh", "nginx"):
            stub = self.bin / name
            stub.write_text("#!/usr/bin/env python3\nimport json,os,sys\n"
                            "from pathlib import Path\n"
                            "Path(os.environ['CHILD_RECORD']).write_text(json.dumps({"
                            "'args':sys.argv[1:],'secret_names':[k for k in "
                            "('TPE_AI_API_KEY','VAST_SSH_PRIVATE_KEY_B64','VAST_SSH_KNOWN_HOSTS') "
                            "if k in os.environ]}))\n")
            stub.chmod(0o755)

    def start(self, service, **env):
        return subprocess.run(["sh", str(ROOT / "docker" / service / "start.sh")],
                              env={**self.env, **env}, capture_output=True, text=True)

    def test_gateway_writes_private_token_file_and_clears_child_secret(self):
        token = "test_" + "a" * 40
        result = self.start("gateway", TPE_AI_API_KEY=token)
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.run / "tokens.conf"
        self.assertEqual(path.read_text(), f'"Bearer {token}" tpe;\n')
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(json.loads(self.child.read_text())["secret_names"], [])
        self.assertNotIn(token, result.stdout + result.stderr)

    def test_gateway_rejects_empty_short_or_configuration_injection_tokens(self):
        for token in ("", "short", "a" * 129, 'a"; include /tmp/anything; #'):
            with self.subTest(token=token):
                result = self.start("gateway", TPE_AI_API_KEY=token)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(self.child.exists())

    def test_tunnel_requires_credentials(self):
        result = self.start("tunnel", VAST_SSH_HOST="gpu.example.com", VAST_SSH_PORT="2222",
                            VAST_SSH_PRIVATE_KEY_B64="", VAST_SSH_KNOWN_HOSTS="")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.child.exists())

    @unittest.skipUnless(shutil.which("ssh-keygen"), "ssh-keygen is required")
    def test_tunnel_checks_endpoint_and_private_key_before_connecting(self):
        key = self.root / "test_key"
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)], check=True)
        encoded = base64.b64encode(key.read_bytes()).decode()
        values = dict(VAST_SSH_HOST="gpu.example.com", VAST_SSH_PORT="2222",
                      VAST_SSH_USER="root", VAST_SSH_PRIVATE_KEY_B64=encoded,
                      VAST_SSH_KNOWN_HOSTS="[gpu.example.com]:2222 " + key.with_suffix(".pub").read_text())
        result = self.start("tunnel", **values)
        self.assertEqual(result.returncode, 0, result.stderr)
        child = json.loads(self.child.read_text())
        self.assertEqual(child["secret_names"], [])
        self.assertIn("StrictHostKeyChecking=yes", child["args"])
        self.assertIn("ExitOnForwardFailure=yes", child["args"])
        self.assertIn("127.0.0.1:11434:127.0.0.1:11434", child["args"])
        self.assertEqual(stat.S_IMODE((self.run / "id_ed25519").stat().st_mode), 0o600)
        self.assertNotIn(encoded, result.stdout + result.stderr)

        self.child.unlink()
        values["VAST_SSH_HOST"] = "different.example.com"
        result = self.start("tunnel", **values)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.child.exists())

        values["VAST_SSH_HOST"] = "gpu.example.com"
        values["VAST_SSH_PRIVATE_KEY_B64"] = base64.b64encode(b"not a private key").decode()
        result = self.start("tunnel", **values)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.child.exists())
