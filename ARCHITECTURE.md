# Architecture

The deployment has one Komodo Stack on the existing tpe-px1-rmt1 and one remote Vast GPU worker.

## Responsibilities

| Owner | Responsibility |
|---|---|
| tpe-ai-stack in Komodo | Start the local API and SSH connection; supply connection settings and credentials |
| tpe-ai-worker.yml | Configure the prepared Vast container's model settings and reconcile Ollama/bootstrap processes |
| Vast worker image | Provide Ollama, supervisor, model cache and the restart entrypoint |

The local API forwards requests over SSH to Ollama bound to 127.0.0.1:11434 inside the worker. The API container shares the SSH container's network namespace, so that socket remains local to the pair.

On the host the API is published only at 127.0.0.1:11435. Same-host containers can join the tpe-ai Docker network and address tpe-ai-api:8080. Both paths require the API token. The SSH connection encrypts traffic between the host and Vast.

## Ownership and credentials

Komodo secret variables are the runtime source for the API token and dedicated worker SSH private key. The key is encoded as one-line base64 for transport, which is not encryption. Startup writes credentials to private tmpfs files and removes them from the child process environment. Docker/Komodo administrators can still inspect the configured environment and must be trusted.

The verified SSH host key is supplied in VAST_SSH_KNOWN_HOSTS. Missing, malformed or mismatched settings fail closed. There are no host secret-file mounts, separate host Ansible role, new host nginx config, certificate or DNS record.

An optional SOPS file is an offline record only; changing it does not update Komodo automatically. Recreate both containers when connection settings or credentials change.

## Runtime boundaries

The gateway permits model listing and OpenAI/Anthropic-compatible inference, blocks raw Ollama management routes and limits concurrent generation to one. Only the worker holds model weights. No public Ollama port, tailnet enrollment, paid model endpoint or inference fallback is introduced.

The initial service has one GPU and no automatic rental lifecycle/spend controller. Production availability and workload scheduling remain later work.
