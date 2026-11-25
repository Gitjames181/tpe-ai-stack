# TPE AI Stack

**One Komodo Stack on tpe-px1-rmt1 queries one Vast GPU worker.**

| Location | Runs there | Managed by |
|---|---|---|
| Existing tpe-px1-rmt1 | ai-stack: authenticated API and encrypted SSH connection | Komodo, this repository |
| One Vast GPU rental | Ollama, model weights and inference | Worker image here; tpe-ai-worker.yml in tpe-infrastructure |

The only Ansible addition is [tpe-ai-worker.yml](https://github.com/Gitjames181/tpe-infrastructure/blob/codex/tpe-ai-infrastructure/ansible/playbooks/tpe-ai-worker.yml), tracked in [PR #2](https://github.com/Gitjames181/tpe-infrastructure/pull/2). There is no separate AI host playbook or host DNS/TLS setup.

Set the Vast SSH host, mapped port, verified host key, dedicated SSH key and API token in the Komodo Stack environment. Deploy ai-stack; it connects to the worker. Read [RUNBOOK.md](RUNBOOK.md) for the exact steps.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Browser / Client                            │
│                                                                  │
│  Web UI          API                                             │
│  127.0.0.1:8081  127.0.0.1:11435                                │
└──────────┬──────────────┬────────────────────────────────────────┘
           │              │
           └──────┬───────┘
                  │
         ┌────────▼────────┐
         │  Open WebUI     │  or  Direct API calls
         │  (Docker)       │
         │                 │
         │ 127.0.0.1:8081  │
         └────────┬────────┘
                  │
           Ollama API endpoint
           127.0.0.1:11434
                  │
                  ▼
         ┌──────────────────────┐
         │   SSH TUNNEL         │
         │  (Docker Container)  │
         │                      │
         │  tpe-ai-tunnel:1.0.0 │
         │                      │
         │ • SSH connection     │
         │ • Encryption         │
         │ • Port forwarding    │
         └──────────┬───────────┘
                    │
             SSH tunnel over
           network to Vast worker
                    │
                    ▼
         ┌──────────────────────┐
         │  OLLAMA (Vast GPU)   │
         │  Remote GPU Worker   │
         │                      │
         │  Managed by:         │
         │  tpe-ai-worker.yml   │
         │                      │
         │ • Model inference    │
         │ • CUDA acceleration  │
         │ • Model weights      │
         └──────────────────────┘
```

**Flow:** Browser → Web UI → Ollama API → SSH Tunnel → GPU Inference

## Application endpoint

| Caller | Base URL | Purpose |
|---|---|---|
| Browser (web UI) | http://127.0.0.1:8081 | Ollama Web UI (chat interface) |
| Process on tpe-px1-rmt1 | http://127.0.0.1:11435/v1 | Programmatic API (auth required) |
| Same-host container attached to the tpe-ai network | http://tpe-ai-api:8080/v1 | Programmatic API (auth required) |

Use model **tpe-code:latest** and the configured **TPE_AI_API_KEY** (for API endpoints). The web UI handles authentication separately via **WEBUI_SECRET_KEY**. A laptop can forward the host's loopback port through its existing SSH access. No ai.tpe DNS name is created by this setup.

The stack provides access to the remote Ollama API. The Ollama inference server runs on the GPU worker. A local Ollama server cannot attach to a remote GPU by setting an endpoint.

See [OLLAMA-WEBUI.md](OLLAMA-WEBUI.md) for web UI configuration and troubleshooting.

## What is included

- docker-compose.yml and docker/: the single Komodo Stack.
- vast/: the GPU image, process supervisor and model configuration.
- komodo/: Stack settings, following tpe-support's deployment convention.
- scripts/ and tests/: acceptance checks and source validation.
- [PLAN.md](PLAN.md): deployment sequence.
- [REMAINING-WORK.md](REMAINING-WORK.md): live deployment gates.

The starting model is qwen3-coder:30b with 16K context and one generation at a time. Hardware fit and coding quality require measurement. Cloud inference and paid API fallback are disabled.

## Checks

~~~sh
python3 -m pip install -r requirements-dev.txt
sh scripts/check.sh
~~~

Set NGINX_BINARY to an installed nginx executable for the actual gateway behavior tests; set COMPOSE_BINARY to a standalone Docker Compose executable if needed. Missing tools are reported as skips. No test rents hardware or calls a paid API.

Source is published; live image builds, rental selection, deployment and a real GPU/agent acceptance run remain outstanding.
