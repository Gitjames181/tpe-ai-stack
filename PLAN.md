# TPE AI plan — revised 24 November 2026

Goal: one Komodo Stack on tpe-px1-rmt1 queries one Vast worker, enabling internal development for PROJ15 without paid inference APIs.

## Delivery

1. Publish this stack and the infrastructure PR containing only tpe-ai-worker.yml.
2. Build the worker image from vast/Dockerfile; record and use its immutable image digest.
3. Select one priced Vast GPU offer. Use SSH launch mode and /opt/tpe-ai/start.sh as the on-start command.
4. Run tpe-ai-worker.yml against that rental's public SSH endpoint using a private inventory.
5. Set the connection and secret variables in Komodo; deploy ai-stack on tpe-px1-rmt1.
6. Point a coding client or application at the stack API. Prove streaming, GPU use, one real edit/test cycle and rental restart recovery.
7. Record the accepted image/model versions and operating cost, then resume a bounded PROJ15 task.

There is no additional gateway server or AI host Ansible playbook. All local containers belong to the single ai-stack Komodo deployment.

## Initial workload

Use qwen3-coder:30b as tpe-code:latest, 16,384 context tokens and one generation at a time. A single 24 GB GPU is a pilot candidate; model fit and latency are not established until tested. Larger coding contexts may require more VRAM. Do not assume equivalence to Claude Sonnet.

## Costs

Model subscriptions and paid inference APIs remain excluded. Only infrastructure rental is permitted. No numeric rental limit or specific offer has been selected. Assess compute, disk, bandwidth, contract duration and funding settings before committing; stopped storage can remain billable.

Start with an on-demand trial. Consider a reservation after useful coding work and restart recovery pass. This version contains no automatic rental spend cap.

## Acceptance

- One Komodo Stack reaches one configured Vast worker.
- Requests require authentication; raw Ollama remains private.
- The configured model responds through the API and uses the GPU.
- A coding client completes a real tool/edit/test cycle.
- Worker and tunnel recover after a rental stop/start.
- Exact source, image/model digests and rental cost terms are recorded.

The stated 269 pending PROJ15 tasks have not been marked complete.

## References

- [Ollama local configuration](https://docs.ollama.com/faq)
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
- [Vast Docker environment](https://docs.vast.ai/guides/instances/docker-environment)
- [Vast pricing](https://docs.vast.ai/guides/instances/pricing)
