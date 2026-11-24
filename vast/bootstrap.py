#!/usr/bin/env python3
"""Resolve one local model and freeze its digest before publishing the alias."""
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from config import load_config, normalize_digest

BASE = "http://127.0.0.1:11434"
LOCK = Path("/workspace/tpe-ai/model-lock.json")

def request(path, payload=None, timeout=30):
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)

def check_digest(config, digest, previous=None):
    digest = normalize_digest(digest)
    expected = config.get("expected_digest")
    if not expected and previous:
        if previous.get("source_model") != config["source_model"]:
            raise ValueError("Changing the source model requires an explicit expected_digest")
        expected = normalize_digest(previous["source_digest"])
    if expected and expected != digest:
        raise ValueError("Model digest changed; review and explicitly update expected_digest")
    return digest

def main():
    config = load_config()
    for _ in range(60):
        try:
            request("/api/version")
            break
        except (OSError, urllib.error.URLError):
            time.sleep(2)
    else:
        raise RuntimeError("Ollama did not become reachable")

    previous = json.loads(LOCK.read_text()) if LOCK.exists() else None
    # Only the first install (or an explicit reviewed update) pulls a moving tag.
    models = request("/api/tags")["models"]
    source = next((m for m in models if m["name"] == config["source_model"]), None)
    if source is None or (config["expected_digest"] and source["digest"] != config["expected_digest"]):
        request("/api/pull", {"model": config["source_model"], "stream": False}, timeout=3600)
        source = next(m for m in request("/api/tags")["models"] if m["name"] == config["source_model"])
    digest = check_digest(config, source["digest"], previous)
    request("/api/create", {
        "model": config["model_alias"], "from": config["source_model"],
        "parameters": {"num_ctx": config["context_length"]}, "stream": False
    }, timeout=300)
    request("/api/show", {"model": config["model_alias"]})
    lock = {
        "source_model": config["source_model"], "source_digest": digest,
        "model_alias": config["model_alias"], "context_length": config["context_length"],
        "ollama_version": request("/api/version")["version"]
    }
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    tmp = LOCK.with_suffix(".tmp")
    tmp.write_text(json.dumps(lock, indent=2) + "\n")
    os.replace(tmp, LOCK)
    print(json.dumps({"status": "model_installed", **lock}), flush=True)

if __name__ == "__main__":
    main()
