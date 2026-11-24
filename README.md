# TPE AI Stack

Private AI inference for PROJ15, initially one coding session and later shared services for the TPE software stack. Model subscriptions and paid inference APIs are disabled; rented GPU capacity is the permitted running cost.

This repository follows tpe-support's layout and Komodo deployment pattern, with its own stack name **ai-stack**. It does not include telephony components.

## Placement

| Component | Location | Responsibility |
|---|---|---|
| Host nginx | tpe-px1-rmt1 | Private HTTPS entrypoint, ai.tpe |
| Gateway container | tpe-px1-rmt1 | Caller authentication, concurrency limit, streaming, API allowlist |
| SSH tunnel container | tpe-px1-rmt1 | Reconnecting private connection to the selected Vast instance |
| Ollama | Vast GPU rental | Local model inference, cloud features disabled |
| Coding agent and source checkout | Developer machine or trusted TPE runner | File edits, builds and tests |

Ollama must run on the machine with the GPU. Installing it only on the VPS does not attach a remote GPU.

## Current delivery state

The repository contains the gateway, tunnel, Vast image/profile, acceptance script, tests and deployment plan. **A source commit is not a deployment.** Live server access, an actual Vast offer, runtime image publication, credentials, TLS and a real GPU/agent acceptance run remain deployment prerequisites.

Host integration is tracked in [tpe-infrastructure PR #2](https://github.com/Gitjames181/tpe-infrastructure/pull/2). Read [PLAN.md](PLAN.md) for the delivery sequence and [RUNBOOK.md](RUNBOOK.md) for execution.

The initial model is qwen3-coder:30b, exposed as tpe-code:latest with 16,384 tokens and one generation at a time. This is a bounded pilot configuration; it is not a claim of Claude Sonnet equivalence or suitability for every PROJ15 task.

## Repository layout

| Path | Purpose |
|---|---|
| docker-compose.yml | VPS gateway and tunnel |
| docker/gateway/ | Native multi-architecture nginx image and API policy |
| docker/tunnel/ | OpenSSH client image and validated startup |
| vast/ | Ollama image, process supervisor, model configuration and digest lock |
| komodo/ai-stack.toml | Stack intent; automatic deployment disabled |
| secrets/ | Placeholder schema and SOPS convention |
| scripts/smoke.py | Live authentication, isolation, readiness and streaming checks |
| tests/ | Gateway behavior, model policy and SSH input tests |
| PLAN.md | Objective, delivery sequence, cost policy and future expansion |
| RUNBOOK.md | Build, deploy, validate and recover |
| REMAINING-WORK.md | Explicit live validation and later work |

## Configuration ownership

tpe-infrastructure owns /etc/tpe-ai, dedicated TLS material, the host nginx vhost and Technitium DNS. Komodo owns the stack checkout and container deployment. No second Ansible-managed Compose copy is created.

The gateway and tunnel share a container network namespace, so the gateway can reach the tunnel on its own loopback. The only Docker port publication is 127.0.0.1:11435. Container clients call https://ai.tpe/v1 through host nginx; they must not use their own localhost.

Komodo Resource Sync remains disabled under the policy recorded in tpe-support/AGENTS.md. Configure ai-stack in the Komodo UI, using the TOML as a reference; verify the actual registered Server name. auto_update is false.

## Local checks

Python 3.11+ and requirements-dev.txt are needed for tests:

~~~sh
python3 -m pip install -r requirements-dev.txt
sh scripts/check.sh
~~~

To exercise the real nginx policy against an isolated mock backend, set NGINX_BINARY to an installed nginx executable. To validate Compose without a Docker daemon, set COMPOSE_BINARY to the official standalone Compose executable. Without these tools the corresponding checks are reported as skipped.

No test calls a paid API or rents hardware. Docker image builds, an actual ARM64 deployment and a live GPU test remain separate gates.

Read RUNBOOK.md before deployment.
