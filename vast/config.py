"""Validated, non-secret inference configuration."""
import json
import re
from pathlib import Path

def normalize_digest(digest):
    if not isinstance(digest, str) or not re.fullmatch(r"(?:sha256:)?[a-f0-9]{64}", digest):
        raise ValueError("expected_digest must be a full SHA-256 digest")
    return digest.removeprefix("sha256:")

def load_config(path="/etc/tpe-ai/worker.json"):
    config = json.loads(Path(path).read_text())
    model = config.get("source_model", "")
    if not re.fullmatch(r"[A-Za-z0-9_.:/-]+", model) or "cloud" in model.lower():
        raise ValueError("source_model must be a local Ollama model, never a cloud model")
    if config.get("model_alias") != "tpe-code:latest":
        raise ValueError("model_alias must match the gateway contract: tpe-code:latest")
    context = config.get("context_length")
    if type(context) is not int or not 2048 <= context <= 65536:
        raise ValueError("context_length must be an integer from 2048 to 65536")
    digest = config.get("expected_digest", "")
    config["expected_digest"] = normalize_digest(digest) if digest else ""
    return config
