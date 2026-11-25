# NGINX Migration: Docker to Production Build

## Overview

The tpe-ai-stack previously shipped NGINX as a containerized Docker service (gateway) that proxied requests to Ollama via the SSH tunnel. This has been refactored to use the production-hardened NGINX build from [tpe-nginx-artefact](../tpe-nginx-artefact) — built from source with HTTP/3, ModSecurity v3, Brotli, jemalloc, and other production modules.

## Changes Made

### Removed
- **docker/gateway/** — Dockerfile, nginx.conf, proxy.conf, start.sh
- **gateway service** in docker-compose.yml

### Added
- **nginx/** directory with production configurations:
  - `nginx.conf` — Main server configuration (uses jemalloc, compression, ModSecurity)
  - `conf.d/ai-gateway.conf` — Virtual host (127.0.0.1:11435)
  - `ai-proxy.conf` — Proxy settings (streaming, timeouts, error handling)
  - `modsecurity/modsecurity.conf` — WAF rules (detection-only mode)
  - `README.md` — Deployment and configuration guide

## Deployment

### 1. Install the production NGINX package

```bash
# Download from tpe-nginx-artefact/published/
sudo dpkg -i nginx-modsecurity-quic_1.0.0_amd64.deb
```

### 2. Deploy configurations

```bash
# Copy main config
sudo cp nginx/nginx.conf /etc/nginx/nginx.conf

# Copy site configs
sudo cp -r nginx/conf.d/* /etc/nginx/conf.d/

# Copy ModSecurity rules
sudo cp -r nginx/modsecurity/* /etc/nginx/modsecurity/
```

### 3. Create runtime directories

```bash
# Owned by nginx user (created by postinst)
sudo mkdir -p /run/ai
sudo chown nginx:nginx /run/ai
sudo chmod 0700 /run/ai
```

### 4. Verify and start

```bash
# Check syntax
sudo nginx -t

# Restart service
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Architecture Change

**Before (Docker):**
```
Client → Docker Gateway (nginx:1.30.8-alpine)
       → SSH Tunnel Container
       → Ollama (Vast GPU)
```

**After (Production):**
```
Client → Host NGINX (tpe-nginx-artefact)
       → Docker Tunnel Container
       → SSH → Ollama (Vast GPU)
```

The gateway no longer runs in a container. It runs natively on the host with:
- Full production capabilities (ModSecurity, Brotli, HTTP/3, etc.)
- Stricter security hardening (capabilities, permissions)
- Same authentication/rate-limiting as before

## Configuration Details

| Setting | Value | Purpose |
|---------|-------|---------|
| Listen | 127.0.0.1:11435 | Localhost only, same port as before |
| Auth | Bearer token from `/run/ai/tokens.conf` | Caller identification |
| Endpoints | /v1/{chat/completions,messages,models}, /healthz, /readyz | OpenAI/Anthropic compatible, health checks |
| Rate limit | 30 req/min per caller, 1 concurrent generation | Prevent abuse |
| Upstream | 127.0.0.1:11434 (SSH tunnel) | Ollama exposed by tpe-ai-tunnel |
| ModSecurity | Detection only, not blocking | Audit mode; logs to modsecurity_audit.log |

## Runtime Integration

The `/run/ai/tokens.conf` file is populated by Komodo at startup. Example:
```
"Bearer sk-tpe-secret-token-12345" "caller-id-1";
"Bearer sk-tpe-secret-token-67890" "caller-id-2";
```

This is generated from `${TPE_AI_API_KEY}` and other secret variables and written by the tunnel container's init script.

## Logs

- **Access:** `/var/log/nginx/access.log` (JSON format with caller, duration, request_id)
- **Errors:** `/var/log/nginx/error.log`
- **ModSecurity:** `/var/log/nginx/modsecurity_audit.log` (WAF audit trail)

## Verification

Run the smoke test:
```bash
./scripts/smoke.py
```

Health check:
```bash
curl http://127.0.0.1:11435/healthz
```

Authenticated check:
```bash
curl -H "Authorization: Bearer <TOKEN>" \
  http://127.0.0.1:11435/readyz
```

## Troubleshooting

### NGINX fails to start
```bash
sudo nginx -t  # Check syntax errors
sudo journalctl -u nginx -n 20  # Recent logs
```

### Upstream connection errors (502/504)
- Verify tunnel container is running: `docker compose ps`
- Check SSH connection: `docker compose logs tunnel`
- Verify 127.0.0.1:11434 is reachable from host

### Authentication failures (401)
- Verify `/run/ai/tokens.conf` exists and contains bearer tokens
- Check NGINX config: `sudo cat /etc/nginx/conf.d/ai-gateway.conf`

### Rate limiting / 429 errors
- Configuration: 30 requests per minute per caller
- Burst capacity: 5 requests
- Concurrent generations: 1 (queued after first)
