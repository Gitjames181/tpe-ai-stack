# Architecture

The deployment has one Komodo Stack on the existing tpe-px1-rmt1 and one remote Vast GPU worker.

## Responsibilities

| Owner | Responsibility |
|---|---|
| tpe-ai-stack in Komodo | Start the web UI, API gateway, SSH tunnel; supply connection settings and credentials |
| tpe-ai-worker.yml (tpe-infrastructure) | Configure the prepared Vast container's model settings and reconcile Ollama/bootstrap processes |
| Vast worker image | Provide Ollama, supervisor, model cache and the restart entrypoint |

The local API and web UI forward requests over SSH to Ollama bound to 127.0.0.1:11434 inside the worker. The tunnel container shares the SSH namespace for local socket access.

On the host the services are published at:
- **127.0.0.1:8081** — Ollama Web UI (Open WebUI)
- **127.0.0.1:11435** — NGINX API gateway (requires TPE_AI_API_KEY)

Same-host containers can join the tpe-ai Docker network and address tpe-ai-api:8080. Both paths require authentication. The SSH connection encrypts traffic between the host and Vast.

## Ownership and credentials

Komodo secret variables are the runtime source for:
- API token (TPE_AI_API_KEY) — for NGINX gateway auth
- Web UI signing key (WEBUI_SECRET_KEY) — for session auth
- SSH private key (VAST_SSH_PRIVATE_KEY_B64) — for Vast connection

The key is encoded as one-line base64 for transport, which is not encryption. Startup writes credentials to private tmpfs files and removes them from the child process environment. Docker/Komodo administrators can still inspect the configured environment and must be trusted.

The verified SSH host key is supplied in VAST_SSH_KNOWN_HOSTS. Missing, malformed or mismatched settings fail closed. There are no host secret-file mounts, separate host Ansible role, new host nginx config, certificate or DNS record.

An optional SOPS file is an offline record only; changing it does not update Komodo automatically. Recreate both containers when connection settings or credentials change.

## Runtime boundaries

The gateway permits model listing and OpenAI/Anthropic-compatible inference, blocks raw Ollama management routes and limits concurrent generation to one. The web UI provides a browsable chat interface with account isolation. Only the worker holds model weights. No public Ollama port, tailnet enrollment, paid model endpoint or inference fallback is introduced.

The initial service has one GPU and no automatic rental lifecycle/spend controller. Production availability and workload scheduling remain later work.

## Related documentation

- [INTEGRATION.md](INTEGRATION.md) — Relationship between this stack and tpe-infrastructure
- [OLLAMA-WEBUI.md](OLLAMA-WEBUI.md) — Web UI setup and configuration
- [../tpe-infrastructure/ansible/playbooks/tpe-ai-worker.yml](../tpe-infrastructure/ansible/playbooks/tpe-ai-worker.yml) — Worker playbook
