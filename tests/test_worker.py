import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vast"))
from config import load_config
from bootstrap import check_digest

D1 = "a" * 64
D2 = "b" * 64

class WorkerPolicyTests(unittest.TestCase):
    def config(self, **values):
        config = {"source_model": "qwen3-coder:30b", "model_alias": "tpe-code:latest",
                  "context_length": 16384, "expected_digest": ""}
        config.update(values)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "worker.json"
            path.write_text(json.dumps(config))
            return load_config(path)

    def test_local_model_is_accepted(self):
        self.assertEqual(self.config()["context_length"], 16384)

    def test_native_ollama_digest_and_prefixed_digest_match(self):
        for digest in (D1, "sha256:" + D1):
            self.assertEqual(check_digest(self.config(expected_digest=digest), D1), D1)

    def test_short_digest_is_refused(self):
        with self.assertRaises(ValueError):
            self.config(expected_digest="06c1097efce0")

    def test_cloud_models_are_refused(self):
        for name in ("qwen3-coder:480b-cloud", "model:cloud", "https://ollama.com/cloud"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.config(source_model=name)

    def test_invalid_context_and_alias_are_refused(self):
        for value in (True, -1, 200000, "16384"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.config(context_length=value)
        with self.assertRaises(ValueError):
            self.config(model_alias="other")

    def test_moving_tag_cannot_silently_replace_the_locked_model(self):
        previous = {"source_model": "qwen3-coder:30b", "source_digest": D1}
        self.assertEqual(check_digest(self.config(), D1, previous), D1)
        with self.assertRaises(ValueError):
            check_digest(self.config(), D2, previous)

    def test_explicit_digest_permits_reviewed_update(self):
        previous = {"source_model": "old", "source_digest": D1}
        self.assertEqual(check_digest(self.config(expected_digest=D2), D2, previous), D2)

    def test_model_change_needs_an_explicit_digest(self):
        with self.assertRaises(ValueError):
            check_digest(self.config(), D1, {"source_model": "other", "source_digest": D1})

if __name__ == "__main__":
    unittest.main()
