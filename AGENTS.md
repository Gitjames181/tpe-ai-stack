# TPE AI Stack

GitOps source for private TPE inference access. Pattern: tpe-support; stack ai-stack, checkout /opt/stacks/tpe-ai-stack, branch main.

- Keep model subscriptions and paid inference APIs disabled. Only server rental is permitted.
- tpe-px1-rmt1 runs the gateway and SSH tunnel; Ollama runs on the rented GPU.
- Never commit plaintext credentials, private keys, decrypted SOPS files or model weights.
- Host DNS, TLS, secret delivery and nginx are owned by tpe-infrastructure.
- Komodo Resource Sync remains disabled by policy. Its TOML documents the intended Stack; configure/deploy through Komodo explicitly. auto_update must remain false.
- No host networking and no publicly published inference port. Gateway publishes only 127.0.0.1:11435.
- The gateway shares the tunnel container's network namespace. Its loopback upstream is intentional; host.docker.internal would not reach a host-loopback listener.
- This is a persistent inference service. Do not attach it to enrichment-session teardown.
- Pin runtime versions; record exact built image and model digests before long-term rental.
- Read RUNBOOK.md before deployment. Run scripts/check.sh for changes. Container/GPU checks remain required on the deployment hosts.
- Do not copy telephony-specific settings, secrets or runtime debt from tpe-support.
