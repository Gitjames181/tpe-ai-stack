#!/usr/bin/env python3
"""Authenticated end-to-end checks. Never prints credentials or prompt bodies."""
import argparse
import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:11435")
    parser.add_argument("--ca-file", default=os.environ.get("TPE_AI_CA_FILE"))
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    parsed = urllib.parse.urlsplit(base)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise SystemExit("Use an endpoint URL without credentials, query or fragment")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in ("localhost", "127.0.0.1", "::1")
    ):
        raise SystemExit("HTTP is allowed only over loopback; use HTTPS for remote endpoints")
    token = os.environ.get("TPE_AI_API_KEY")
    if not token:
        raise SystemExit("Set TPE_AI_API_KEY securely")
    context = ssl.create_default_context(cafile=args.ca_file)
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    opener = urllib.request.build_opener(NoRedirect(), urllib.request.HTTPSHandler(context=context))
    def call(path, payload=None, credential=token):
        headers = {"Content-Type": "application/json"}
        if credential:
            headers["Authorization"] = "Bearer " + credential
        body = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request(base + path, data=body, headers=headers)
        return opener.open(request, timeout=600)

    for credential in (None, "invalid"):
        try:
            with call("/v1/models", credential=credential):
                raise RuntimeError("Unauthenticated request was accepted")
        except urllib.error.HTTPError as error:
            if error.code != 401:
                raise
    try:
        with call("/api/tags"):
            raise RuntimeError("Ollama management API was exposed")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    with call("/readyz") as response:
        json.load(response)
    with call("/v1/models") as response:
        models = json.load(response)["data"]
        assert any(m["id"] == "tpe-code:latest" for m in models), "Alias missing"
    payload = {
        "model": "tpe-code:latest",
        "messages": [{"role": "user", "content": "Reply with one word: ready"}],
        "max_tokens": 16, "stream": True
    }
    saw_text = False
    saw_done = False
    with call("/v1/chat/completions", payload) as response:
        for raw in response:
            line = raw.decode().strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                saw_done = True
                continue
            event = json.loads(data)
            if event.get("error"):
                raise RuntimeError("Streaming inference returned an error")
            for choice in event.get("choices", []):
                saw_text |= bool(choice.get("delta", {}).get("content"))
    if not saw_text or not saw_done:
        raise RuntimeError("Incomplete streaming response")
    print("PASS: auth rejection, management isolation, alias readiness and streamed inference")
    print("Still required: real agent edit/test cycle, GPU residency and stop/start recovery.")

if __name__ == "__main__":
    main()
