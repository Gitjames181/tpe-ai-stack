"""Contract checks for exposure and the shared tunnel namespace."""
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]

class ComposeBoundaryTests(unittest.TestCase):
    def test_only_the_gateway_is_published_on_loopback(self):
        config = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
        self.assertEqual(config["name"], "ai-stack")
        services = config["services"]
        self.assertEqual(services["gateway"]["network_mode"], "service:tunnel")
        self.assertNotIn("ports", services["gateway"])
        for service in services.values():
            self.assertNotEqual(service.get("network_mode"), "host")
            for port in service.get("ports", []):
                self.assertTrue(port.startswith("127.0.0.1:"), port)
                self.assertTrue(port.endswith(":8080"), port)
