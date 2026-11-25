# Integration with tpe-infrastructure

This stack interfaces with the AI worker provisioned and managed by **tpe-infrastructure**.

## Responsibilities

| Repo | Responsibility | Deployment Target |
|------|---|---|
| **tpe-ai-stack** (this) | Web UI, API gateway, SSH tunnel, client interfaces | tpe-px1-rmt1 (Komodo Stack) |
| **tpe-infrastructure** | Worker configuration, model setup, supervision | Vast GPU rental |
| **Vast** | GPU hardware, OS, container runtime | Rented hardware |

## Workflow

### 1. Provision a Vast GPU

Rent a GPU from Vast using their rental API or web interface. You will receive:
- **Host:** e.g., `216.98.123.45`
- **Port:** e.g., `2222` (mapped SSH port)
- **Image:** Vast's pre-built container with Docker
- **Template:** Use `tpe-ai-stack/vast/` as the base image

### 2. Deploy the Worker

Once the Vast container is running with the tpe-ai-stack image:

```bash
# In tpe-infrastructure repo
ansible-playbook -i inventory/vast-ai-hosts tpe-ai-infrastructure/ansible/playbooks/tpe-ai-worker.yml \
  -e "tpe_ai_source_model=qwen3-coder:30b" \
  -e "tpe_ai_context_length=16384"
```

The playbook:
- Verifies the Vast image is installed at `/opt/tpe-ai/start.sh`
- Writes worker configuration to `/etc/tpe-ai/worker.json`
- Starts the supervisor (if not already running)
- Pulls and aliases the model (e.g., `tpe-code:latest`)

### 3. Configure tpe-ai-stack in Komodo

In your Komodo Stack settings, set environment variables:

```
VAST_SSH_HOST: <Vast host IP>
VAST_SSH_PORT: <Mapped SSH port, usually 2222>
VAST_SSH_USER: root
VAST_SSH_PRIVATE_KEY_B64: <base64 encoded SSH private key>
VAST_SSH_KNOWN_HOSTS: <Vast host key>
TPE_AI_API_KEY: <secret token for API>
WEBUI_SECRET_KEY: <secret key for web UI auth>
```

### 4. Deploy tpe-ai-stack

```bash
# From the stack repo, trigger Komodo deployment
# Stack will start tunnel and web UI
docker compose up -d
```

The tunnel connects to Vast using the SSH credentials.

### 5. Test Connectivity

```bash
# Check tunnel is connected
docker compose logs tunnel

# Test inference via web UI
curl http://127.0.0.1:8081

# Test inference via API
curl -H "Authorization: Bearer <TPE_AI_API_KEY>" \
  http://127.0.0.1:11435/v1/models
```

## Configuration Hierarchy

### Non-secret settings

Defined in this repo:
- Model name: `tpe-code:latest` (alias only; source model defined in tpe-ai-worker)
- API ports: 11435 (NGINX), 11434 (tunnel), 8081 (web UI)
- Context length: set via `tpe_ai_context_length` in tpe-infrastructure playbook

### Secret settings

Defined in Komodo Stack (never in this repo):
- SSH credentials for Vast worker
- API authentication tokens
- Web UI signing key

## Model Management

### Adding a new model

1. SSH to Vast worker:
   ```bash
   ssh -p 2222 root@<VAST_HOST>
   ```

2. Pull the model:
   ```bash
   ollama pull llama2:latest
   ```

3. (Optional) Create an alias via tpe-ai-infrastructure:
   ```bash
   # Modify tpe_ai_source_model variable and re-run playbook
   ```

4. Model appears in web UI and API automatically.

### Removing a model

Models are managed on Vast. The stack discovers them via the Ollama API.

```bash
# On Vast
ollama rm llama2:latest
```

## Troubleshooting

### "Cannot connect to worker"

1. Verify Vast is still rented and running
2. Verify SSH credentials in Komodo are correct
3. Check tunnel logs: `docker compose logs tunnel`
4. Verify SSH host key matches:
   ```bash
   ssh-keyscan -p 2222 <VAST_HOST>
   ```

### "Model not found"

1. Check model is pulled on Vast:
   ```bash
   ssh -p 2222 root@<VAST_HOST> ollama list
   ```

2. Verify alias matches expected name in tpe-ai-worker.yml

3. Restart Ollama on Vast:
   ```bash
   ssh -p 2222 root@<VAST_HOST> supervisorctl -c /opt/tpe-ai/supervisord.conf restart ollama
   ```

### "Worker configuration not applied"

The tpe-ai-worker.yml playbook only configures an already-running Vast container. It does not:
- Rent the GPU
- Build the image
- Install Vast's container runtime

If the playbook fails:
1. Verify Vast container is running
2. Verify SSH access works: `ssh -p <PORT> root@<HOST>`
3. Verify `/opt/tpe-ai/start.sh` exists on Vast
4. Re-run the playbook

## Separation by Design

The two repos deliberately do not overlap:

| Feature | tpe-ai-stack | tpe-infrastructure |
|---------|---|---|
| Vast provisioning | ✗ | ✗ |
| SSH tunnel | ✓ | ✗ |
| Web UI | ✓ | ✗ |
| API gateway (NGINX) | ✓ | ✗ |
| Worker Ansible | ✗ | ✓ |
| Model aliasing | ✗ | ✓ |
| Supervisor config | ✗ | ✓ |
| Ollama runtime | ✗ | ✓ |

This separation means:
- Each repo has a single responsibility
- Changes to the web UI don't require Vast redeployment
- Changes to worker config don't require stack redeployment
- Both can be versioned and released independently

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — Stack and worker ownership
- [OLLAMA-WEBUI.md](OLLAMA-WEBUI.md) — Web UI configuration
- [../tpe-infrastructure/ansible/playbooks/tpe-ai-worker.yml](../tpe-infrastructure/ansible/playbooks/tpe-ai-worker.yml) — Worker playbook
