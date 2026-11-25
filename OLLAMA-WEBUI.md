# Ollama Web UI Service

The Ollama Web UI (Open WebUI) runs as a Docker container in this stack and provides a browser-based interface to the remote Ollama inference engine on Vast.

## Architecture

```
Browser → Open WebUI (127.0.0.1:8081)
              ↓
         HTTP to Ollama API
              ↓
         127.0.0.1:11434 (SSH tunnel endpoint)
              ↓
         SSH Tunnel (tpe-ai-tunnel container)
              ↓
         Encrypted to Vast GPU
              ↓
         Ollama on Vast (tpe-infrastructure controlled)
              ├─ Model: tpe-code:latest
              └─ Supervised by tpe-ai-worker.yml
```

## Service Details

| Property | Value | Purpose |
|----------|-------|---------|
| Container | `ghcr.io/open-webui/open-webui:latest` | Official Open WebUI image |
| Listen | 127.0.0.1:8081 | Localhost only (default) |
| Upstream | 127.0.0.1:11434 | SSH tunnel to Vast Ollama |
| User | 1000:1000 | Unprivileged |
| Security | read-only FS, no caps, no-new-privileges | Hardened |
| Auth | Enabled (WEBUI_AUTH) | Requires login |
| Default Model | tpe-code:latest | From Vast worker |

## Environment Variables

| Variable | Type | Required | Default | Purpose |
|----------|------|----------|---------|---------|
| `OLLAMA_UI_PORT` | number | no | 8081 | Host port for web UI |
| `WEBUI_SECRET_KEY` | secret | yes | — | Signing key for auth tokens |
| `OLLAMA_BASE_URL` | string | — | (auto) | Ollama API endpoint |
| `WEBUI_AUTH` | boolean | — | true | Require login |

**Setup in Komodo:**
```
OLLAMA_UI_PORT: 8081
WEBUI_SECRET_KEY: <long random string, 32+ chars>
```

## Running Locally

### 1. Start the stack

```bash
docker compose up -d
```

Verify tunnel is running:
```bash
docker compose logs tunnel | head -20
docker compose exec tunnel ping -c 1 127.0.0.1:11434
```

### 2. Access the web UI

```
http://127.0.0.1:8081
```

Create an account on first visit.

### 3. Test inference

- In web UI, select model **tpe-code:latest**
- Send a message
- Response flows: Web UI → Ollama API → Tunnel → Vast → back

### 4. View logs

```bash
docker compose logs ollama-webui -f
docker compose logs tunnel -f
```

## Security

- **Localhost only:** Web UI accessible only from the host machine
- **Authentication required:** WEBUI_AUTH=true enforces login
- **Read-only filesystem:** Container cannot write to the host
- **No capabilities:** CAP_DROP=ALL prevents privilege escalation
- **Encrypted upstream:** All traffic to Vast goes through SSH tunnel
- **Stateless:** Data stored in tmpfs; no persistent data on disk by default

## Configuration

### Persistent User Data

By default, user accounts and chat history are stored in tmpfs (RAM) and lost on container restart.

To persist data, add a volume to `docker-compose.yml`:

```yaml
ollama-webui:
  volumes:
    - webui-data:/home/user/.local
volumes:
  webui-data:
```

### Custom Branding

Modify environment variables in `docker-compose.yml`:
```yaml
environment:
  WEBUI_TITLE: "TPE Code Assistant"
  WEBUI_DEFAULT_MODELS: tpe-code:latest
```

### Additional Models

The web UI will discover any model running on the upstream Ollama instance. To pull a new model on Vast:

```bash
# SSH to Vast worker
# Run: ollama pull <model-name>
```

The web UI will automatically show it.

## Troubleshooting

### "Cannot connect to Ollama"

Check tunnel is running:
```bash
docker compose ps
docker compose logs tunnel
```

Verify 127.0.0.1:11434 is reachable:
```bash
docker compose exec ollama-webui \
  curl -v http://127.0.0.1:11434/api/tags
```

### "Authentication not working"

Verify `WEBUI_SECRET_KEY` is set in Komodo secrets:
```bash
docker compose exec ollama-webui \
  env | grep WEBUI_SECRET
```

### "No models appear"

Models are pulled on Vast and must be in Ollama. Check tpe-ai-worker configuration:
```bash
# On Vast, check supervisord:
supervisorctl status ollama
```

### Performance / High CPU

The web UI may use significant CPU during streaming responses. This is normal for a containerized web service. Monitor with:
```bash
docker stats ollama-webui
```

## Development

### Local Testing Without Vast

You can test the web UI stack locally by running Ollama directly:

```bash
# Terminal 1: Run Ollama locally
ollama serve

# Terminal 2: Run just the web UI with local Ollama
docker run -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -p 8081:8080 \
  ghcr.io/open-webui/open-webui:latest
```

Then access http://localhost:8081

### Customizing the Container

Build a custom image with modifications:
```bash
mkdir -p docker/webui
# Create Dockerfile extending ghcr.io/open-webui/open-webui:latest
docker build -t tpe-webui:latest docker/webui
# Update docker-compose.yml image reference
```

## Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — Stack ownership and boundaries
- [RUNBOOK.md](RUNBOOK.md) — Deployment checklist
- [../tpe-infrastructure/ansible/playbooks/tpe-ai-worker.yml](../tpe-infrastructure/ansible/playbooks/tpe-ai-worker.yml) — Worker configuration on Vast
