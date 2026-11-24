# Runbook

## 1. Start one Vast worker

Build the worker image on a trusted Docker builder:

~~~sh
docker build --platform linux/amd64 -f vast/Dockerfile -t ghcr.io/gitjames181/tpe-ai-worker:0.1.0 .
~~~

Publish it privately and record its immutable digest. Use an image-pull credential limited to that image. In Vast, select SSH launch mode without Jupyter and set the on-start command to /opt/tpe-ai/start.sh. Verify nvidia-smi, the mapped public SSH port and the server host key independently.

Ollama binds to worker loopback. Do not publish port 11434 or run the enrichment tpe-gpu-worker.yml on this container. No host NVIDIA driver or Docker daemon installation is needed inside the rental.

## 2. Run the one Ansible playbook

Create a private inventory outside Git, substituting the actual endpoint:

~~~yaml
all:
  children:
    ai_workers:
      hosts:
        tpe-ai-gpu-01:
          ansible_host: SELECTED_PUBLIC_HOST
          ansible_port: 2222
          ansible_user: root
          ansible_python_interpreter: /usr/bin/python3
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519_tpe_ai
          ansible_ssh_common_args: "-o StrictHostKeyChecking=yes -o UserKnownHostsFile=~/.ssh/tpe-ai-known-hosts"
          tpe_ai_source_model: qwen3-coder:30b
          tpe_ai_context_length: 16384
          tpe_ai_expected_digest: ""
~~~

Use the codex/tpe-ai-infrastructure branch until PR #2 is merged. From tpe-infrastructure/ansible:

~~~sh
ANSIBLE_HOST_KEY_CHECKING=True ansible-playbook -i /secure/ai-workers.yml playbooks/tpe-ai-worker.yml --check --diff
ANSIBLE_HOST_KEY_CHECKING=True ansible-playbook -i /secure/ai-workers.yml playbooks/tpe-ai-worker.yml
~~~

Inspect supervisorctl -c /opt/tpe-ai/supervisord.conf status and /var/log/tpe-ai/bootstrap.log. A successful one-shot bootstrap ends in EXITED; check its completion and /workspace/tpe-ai/model-lock.json rather than assuming any EXITED status is success. Retain the full model digest externally and set tpe_ai_expected_digest before replacing or moving the worker.

## 3. Configure the one Komodo Stack

Use repo Gitjames181/tpe-ai-stack, branch main, Compose file docker-compose.yml, Stack name ai-stack, checkout /opt/stacks/tpe-ai-stack and the existing Server resource for tpe-px1-rmt1. Keep Resource Sync off and auto_update=false.

Set these Stack environment values through Komodo, using secret variables for credentials:

| Variable | Value |
|---|---|
| VAST_SSH_HOST | Rental public SSH host |
| VAST_SSH_PORT | Rental mapped SSH port |
| VAST_SSH_USER | Usually root |
| VAST_SSH_KNOWN_HOSTS | Independently verified OpenSSH record matching that host and port |
| VAST_SSH_PRIVATE_KEY_B64 | Dedicated SSH private key encoded as one-line base64 |
| TPE_AI_API_KEY | 32-128 URL-safe characters |
| AI_GATEWAY_PORT | 11435 unless an existing service uses it |

Encode the key locally without pasting it into chat or logs; base64 does not encrypt it. The key must work without an interactive passphrase because the connection is unattended. Komodo is the runtime source of these secrets; any SOPS copy is an offline record only.

Deploy with image building enabled. The two local containers start as one Stack. No /etc/tpe-ai files, host playbook, AI certificate or DNS record are required. Build the local images natively on the ARM64 VPS.

## 4. Point the application at the stack

For a process on tpe-px1-rmt1, use http://127.0.0.1:11435/v1. For another container on the same Docker host, attach it to the existing tpe-ai network and use http://tpe-ai-api:8080/v1:

~~~yaml
services:
  your_application:
    networks: [existing_application_network, tpe_ai]
networks:
  tpe_ai:
    external: true
    name: tpe-ai
~~~

Keep its existing networks. Supply the model tpe-code:latest and TPE_AI_API_KEY through that application's normal secret configuration. Containers cannot reach the host service using their own localhost.

For a laptop, forward the host-loopback port over existing SSH access and use the forwarded localhost endpoint. An ai.tpe HTTPS URL would require a separate deliberate addition to the existing ingress, and is not created by this stack.

Ollama inference runs on Vast. A local Ollama CLI can target a remote Ollama server, but this authenticated application API does not expose the CLI's native management routes. Use an OpenAI/Anthropic-compatible application client here.

## 5. Check the complete path

Inject TPE_AI_API_KEY and run this on the host, or against the laptop's SSH-forwarded localhost port:

~~~sh
python3 scripts/smoke.py --base-url http://127.0.0.1:11435
~~~

Then observe ollama ps and nvidia-smi on the worker during inference, complete a real coding tool/edit/test cycle, and stop/start the rental to verify worker and SSH recovery. The default 16K context is a limited pilot and may be too small for large coding-agent sessions.

## Changes and recovery

After an endpoint or credential change, redeploy/recreate both containers together; the gateway shares the tunnel's network namespace. For operator-run equivalent deployment, use docker compose -p ai-stack up -d --build --force-recreate.

A changed host key must be independently verified before updating Komodo. Transport failures return 503; the tunnel reconnects after SSH returns. A model digest mismatch requires an explicit reviewed update. Roll back using the previous Stack commit/image and worker configuration.

Stop the Stack in Komodo to withdraw local access. Rental termination is a separate provider action. Export model locks before destruction and check retained storage charges. No automatic rental cost cap is implemented.
