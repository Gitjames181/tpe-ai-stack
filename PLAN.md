# TPE AI infrastructure implementation plan

Decision date: 24 November 2026. Project: PROJ15.
Target: a persistent internal AI endpoint, powered by a rented Vast GPU, that can complete a real development task today if access and hardware are available.

The user reports 269 pending software-stack tasks. This work enables their execution; it does not mark those tasks complete or establish their remaining effort.

## Adopted direction

Keep the persistent gateway on tpe-px1-rmt1 and run Ollama on the Vast GPU. Use the new private GitHub repository Gitjames181/tpe-ai-stack for the application stack, following tpe-support. Add host prerequisites and a distinct AI worker playbook to tpe-infrastructure.

The immediate budget policy is zero model subscriptions and zero paid inference APIs. Vast server rental is allowed. No numerical rental cap or selected offer has been supplied; no rental, prepayment or recurring charge is authorized by a fabricated dollar amount.

## Repository findings that shape the build

Reviewed tpe-infrastructure main at a300e12fe41df517d8924ad7fe800f8e8a72481b and tpe-support main at 992a03f75c594662a6d59f7e97ce44bfdc782ebf.

- The infrastructure records tpe-px1-rmt1 as ARM64, with VPN IP 100.64.0.2. The gateway uses native multi-architecture nginx/Alpine images.
- The existing tpe-gpu-worker.yml is a session-scoped enrichment provisioner with host-driver/systemd assumptions. Its media callback and teardown are not reused for persistent LLM inference.
- Application stacks belong to their repositories and Komodo. Ansible owns host configuration and secrets; it must not recreate a competing Compose stack.
- Ansible control access uses public IPs. Private service traffic uses the VPN/loopback tiers.
- The internal certificate list does not include ai.tpe; its existing renewal check only checks for authentik.tpe. Merely adding a name to that list would not reliably rotate a deployed certificate. This build uses dedicated AI certificate material instead.
- tpe-support's agent instructions say Resource Sync is disabled by policy. The new manifest preserves that policy and uses the correct ai-stack name.

Repository files establish intended configuration, not current live-server health.

## Initial rental specification

| Item | Pilot target |
|---|---|
| GPU | One RTX 3090 24 GB; compare a 4090 only if the actual offer is worthwhile |
| Runtime | Vast Docker instance, SSH launch mode, prepared Ollama image |
| Model | qwen3-coder:30b, inspected Q4_K_M distribution |
| Context and concurrency | 16,384 tokens, one generation |
| Disk | Plan roughly 80-100 GB for image, weights, cache and working headroom; select before launch |
| Allocated system memory | Prefer at least 32 GB for headroom; verify the actual allocation |
| Host | Verified provider; prefer a suitable secure datacenter for private code; assess reliability, latency and contract duration |
| Rental type | On-demand for the pilot; consider a reservation after accepted work and recovery tests |
| Naming | Logical worker tpe-ai-gpu-01; purpose persistent-inference |

Ollama lists the selected 30B package at about 19 GB. Remaining GPU memory must cover context/cache/runtime overhead. Fit and speed are not yet measured. Ollama's coding guidance recommends larger context windows; 16K is a deliberate limited pilot, not a promise that a large repository or Claude Code's full context will fit. Use scoped files/tasks and test compaction; use more VRAM if measured work requires 64K or more.

## Delivery sequence for today

These are estimates after credentials, image access and a suitable offer are available, not a guaranteed deadline.

| Step | Outcome | Estimated focused time |
|---|---|---|
| AI-01 | Publish the private stack repository and review the infrastructure branch | 20-40 min |
| AI-02 | Build native VPS images and the amd64 Vast image; record image digests | 30-60 min |
| AI-03 | Select one priced offer, record its full rental terms, launch and confirm NVIDIA access | 20-40 min plus download time |
| AI-04 | Pull the coding model, record its digest, validate alias and GPU placement | 20-60 min |
| AI-05 | Apply host Ansible configuration, private DNS/TLS and Komodo stack deployment | 30-60 min |
| AI-06 | Pass streamed inference, tool-use/edit/test and recovery acceptance | 45-90 min |
| AI-07 | Freeze the working release; select the first bounded PROJ15 task | 15-30 min |

Model downloads, access issues and slow hosts can extend these estimates. The target is one proven working development loop, followed by evidence-based expansion.

## Definition of done

1. Private source repository and infrastructure changes are committed; the deployment records exact commits and built image digests.
2. ai.tpe resolves privately and client certificate verification succeeds.
3. Anonymous/wrong-key requests fail; Ollama management APIs remain inaccessible; no raw public inference endpoint answers.
4. Model metadata, streamed response and a full tool-call/result cycle work through the gateway.
5. The coding agent reads a scoped repository task, edits files, runs the appropriate check and produces a reviewable change.
6. GPU use and context fit are observed; unintended CPU offload is resolved or explicitly accepted with measured latency.
7. The instance restarts successfully, the on-start command restores the processes, and the gateway reconnects.
8. The actual offer, instance ID, cost components, contract expiry and stop/destruction behavior are recorded.
9. No paid inference endpoint, cloud-model default or paid fallback is configured.

## Cost policy and reservation decision

Self-hosting moves inference spending into infrastructure rental. It does not make compute free or itself prove savings versus the present coding setup.

Illustrative arithmetic only, not live offers:

| Compute rate | 8 hours/day for 30 days | Continuous 30 days |
|---|---:|---:|
| $0.20/hour | $48 | $144 |
| $0.30/hour | $72 | $216 |
| $0.50/hour | $120 | $360 |

Storage, bandwidth, taxes and conversion costs are additional. A stopped instance may continue accruing storage charges and releases its GPU. Destroying it removes its instance data. A reservation is a prepayment tied to a particular instance and is less flexible than an uncommitted pilot.

Before starting, record the selected offer's actual all-in estimate and funded balance/automatic recharge settings. For an unattended trial, provision an independent controller-side stop/expiry mechanism first. This initial repository does not claim an implemented spending cap or automatic lifecycle controller.

For ongoing internal service, choose operating hours deliberately. Keep an always-on gateway; choose an always-on GPU only when the rental budget and workload warrant it. Reserve only after useful work, runtime stability and recovery are demonstrated.

## After the first accepted task

Run a small representative pilot across Laravel, Vue/Next.js, Python and infrastructure work. Measure accepted changes, time, retries and review corrections. Use that evidence to order and estimate the remaining PROJ15 tasks.

Later, add separate application credentials and workload priorities, embeddings, monitoring and provider lifecycle automation. Production-critical applications need a queue/degraded mode or additional capacity; one marketplace rental is not high availability.

## Sources

- [Infrastructure constitution](https://github.com/Gitjames181/tpe-infrastructure/blob/main/CONSTITUTION.md)
- [Existing GPU playbook](https://github.com/Gitjames181/tpe-infrastructure/blob/main/ansible/playbooks/tpe-gpu-worker.yml)
- [Compute playbook](https://github.com/Gitjames181/tpe-infrastructure/blob/main/ansible/playbooks/tpe-px1-rmt1.yml)
- [Support stack instructions](https://github.com/Gitjames181/tpe-support/blob/main/AGENTS.md)
- [Ollama local-only configuration](https://docs.ollama.com/faq)
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
- [Ollama Claude Code integration](https://docs.ollama.com/integrations/claude-code)
- [Ollama context length](https://docs.ollama.com/context-length)
- [Qwen3-Coder 30B distribution](https://ollama.com/library/qwen3-coder:30b)
- [Vast container environment](https://docs.vast.ai/guides/instances/docker-environment)
- [Vast templates](https://docs.vast.ai/guides/templates/template-settings)
- [Vast pricing](https://docs.vast.ai/guides/instances/pricing)
- [Vast reserved instances](https://docs.vast.ai/guides/instances/choosing/reserved-instances)
