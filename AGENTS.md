# TPE AI Stack

One Komodo Stack on tpe-px1-rmt1 queries one Vast GPU worker.
Stack: ai-stack. Checkout: /opt/stacks/tpe-ai-stack. Branch: main.

- The only AI Ansible addition is tpe-infrastructure/ansible/playbooks/tpe-ai-worker.yml, targeting the Vast container.
- Komodo owns this stack's connection settings and runtime secrets. No separate AI host playbook, /etc/tpe-ai dependency, host nginx, TLS or DNS changes.
- The two local containers are the authenticated API and its SSH connection; all model inference runs on the Vast GPU.
- Never commit plaintext secrets, private keys or weights. Komodo secret variables are the runtime source; a SOPS file may be retained only as an explicitly labelled offline record.
- Resource Sync stays disabled and auto_update=false, following tpe-support's current policy.
- Keep host publication on 127.0.0.1:11435. Same-host applications may join the tpe-ai Docker network and use tpe-ai-api:8080 with authentication.
- The gateway shares the tunnel's network namespace; its upstream is container loopback. Never publish raw Ollama.
- Use strict SSH host-key checking with an independently verified key. Do not log secrets.
- No paid inference APIs, cloud models or paid fallback.
- Keep persistent inference independent of enrichment-session teardown.
- Run scripts/check.sh for code changes. Container builds and live GPU/agent/restart checks remain required.
