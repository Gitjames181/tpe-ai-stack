# Architecture

## Service contract

Clients use https://ai.tpe/v1 with a dedicated Bearer credential. The first model alias is tpe-code:latest. Supported public paths are GET /v1/models, POST /v1/chat/completions and POST /v1/messages. The Anthropic endpoint permits evaluation with the existing Claude Code client; model behavior and API compatibility must be tested independently of the client brand.

The gateway only forwards these paths and an authenticated readiness probe. Ollama's pull/create/delete APIs are inaccessible through it. Caller credentials are stripped before requests reach the GPU host. Logs contain caller label, path, status, latency and request ID, never Authorization headers or request bodies.

One active generation is admitted across callers; excess concurrency returns 429. The initial rate allowance is 30 requests/minute per caller with a small burst. There is no hosted-provider fallback and no gateway database.

## Network boundaries

| Hop | Binding / destination |
|---|---|
| Client to host nginx | The gateway host's VPN IP, HTTPS ai.tpe |
| Host nginx to gateway | Host loopback 127.0.0.1:11435 |
| Gateway to tunnel | Shared container loopback 127.0.0.1:11434 |
| Tunnel to Vast | Public SSH endpoint and its mapped port, verified host key |
| Vast SSH to Ollama | Remote loopback 127.0.0.1:11434 |

The VPS initiates the SSH connection. The rental receives no broad tailnet membership, production database credentials, gateway tokens or deployment key. A dedicated SSH key authorizes access to that rental. The provider's host can still access workloads running there; send only the repository context needed for the task.

Ansible's control connection also uses the public SSH endpoint and mapped port. This container profile does not apply OS, firewall, NVIDIA-driver, systemd or nested-Docker roles inside the Vast container. Vast also offers VMs, but that is a different deployment profile.

## Runtime and persistence

The Vast image starts Ollama and model bootstrap under Supervisor. Vast SSH launch mode replaces an image's ENTRYPOINT, so its on-start command must be /opt/tpe-ai/start.sh. The image's default foreground entrypoint also supports isolated local container testing.

Ollama binds loopback, disables cloud features and restricts parallelism to one. Model weights live under /workspace/models; model-lock.json records the resolved digest, runtime version and context setting under /workspace/tpe-ai. These files survive a stop/start of the same retained instance, but must not be treated as durable across destruction or host loss.

The first successful model installation resolves a tag and records its digest. Subsequent starts use the installed model and reject unexplained digest changes. Before migration or a long-term deployment, copy the recorded digest into expected_digest and preserve the lock outside the rental. Version tags are not immutable image digests: record built image digests as part of the release.

The named alias decouples client configuration from the backend model. A failed model update must be investigated through bootstrap logs and the lock: readiness alone only establishes that the alias exists, not that a new desired release succeeded.

## Health meanings

| Signal | What it proves |
|---|---|
| /healthz | Gateway process answers |
| /readyz with valid key | Ollama can describe the coding alias |
| scripts/smoke.py | Authentication rejection, API isolation, alias discovery and a completed streamed response |
| ollama ps plus nvidia-smi during inference | GPU placement and memory behavior |
| A real repository edit/test cycle | The selected client/model can perform useful development work |
| Rental stop/start and tunnel recovery | Operational recovery across the provider boundary |

None of these checks substitutes for the others.

## Future shared service

Keep the stable client URL and separate credentials for development and applications. Add workload-specific models only after the first pilot passes. Embeddings need an embedding model; image/3D work needs its own worker API. The existing enrichment readiness callback and session cleanup must never control this persistent inference rental.

A 24 GB card begins with one workload. Do not run coding and media models concurrently without a VRAM budget and scheduling tests. If application traffic becomes continuous, give it priority or a separate GPU. Consider LiteLLM or another routing layer when multiple models, application quotas or detailed usage accounting justify it; verify native ARM64 support before deployment.
