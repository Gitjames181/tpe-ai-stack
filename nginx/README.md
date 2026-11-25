# TPE AI Stack NGINX Configuration

Configuration for NGINX built from [tpe-nginx-artefact](../tpe-nginx-artefact) — HTTP/3, ModSecurity, Brotli, and production-hardened defaults.

## Directory Structure

```
nginx/
├── README.md                   # This file
├── nginx.conf                  # Main NGINX configuration
├── conf.d/                     # Virtual host and site-specific configs
│   └── ai-gateway.conf         # API gateway configuration
├── modules/                    # Dynamic module configuration
└── modsecurity/                # ModSecurity / OWASP CRS
    ├── modsecurity.conf        # Core WAF settings
    └── owasp-crs/              # OWASP Core Rule Set (from deb install)
```

## Deployment

Install the production NGINX package:
```bash
sudo dpkg -i nginx-modsecurity-quic_1.0.0_amd64.deb
```

Copy configs to system paths:
```bash
sudo cp nginx.conf /etc/nginx/nginx.conf
sudo cp -r conf.d/* /etc/nginx/conf.d/
sudo cp -r modsecurity/* /etc/nginx/modsecurity/
```

Verify syntax:
```bash
sudo nginx -t
```

Start/enable:
```bash
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Configuration

### Main (`nginx.conf`)
- Worker processes: auto
- Upstreams: local tunnel SSH socket forwarded by tpe-ai-tunnel container
- TLS: QUIC/HTTP3, OpenSSL 3.1.4+quic
- Logging: JSON format with caller identification, request tracing

### API Gateway (`conf.d/ai-gateway.conf`)
- Port: 127.0.0.1:11435 (localhost only)
- Authentication: Bearer token from `/run/ai/tokens.conf` (populated by Komodo secrets)
- Endpoints:
  - `GET /v1/models` — list available models
  - `POST /v1/chat/completions` — OpenAI-compatible chat
  - `POST /v1/messages` — Anthropic-compatible messages
  - `GET /healthz` — liveness probe
  - `POST /readyz` — readiness (authenticated)
- Rate limits: 30 req/min per caller, 1 concurrent generation
- Blocks all other routes and Ollama management endpoints

### ModSecurity (`modsecurity/modsecurity.conf`)
- Runs in detection mode (SecAuditEngine On, SecRuleEngine DetectionOnly)
- OWASP CRS enabled but non-blocking (audit only)
- Request/response logging to `/var/log/nginx/modsecurity_audit.log`

## SSH Tunnel Integration

The local tunnel container (`tpe-ai-tunnel:1.0.0`) establishes the SSH connection. NGINX on the host connects upstream to `127.0.0.1:11434` which is Ollama exposed through the tunnel.

```
Client → Host (127.0.0.1:11435) → NGINX auth/rate-limit → SSH tunnel → Ollama (127.0.0.1:11434 on Vast)
```

## Security

- Read-only root filesystem
- CAP_DROP: ALL (minimal capabilities)
- no-new-privileges flag
- Stripped binaries and jemalloc for reliability
- Bearer token auth required for all inference endpoints
- Request/response signatures logged for audit
- ModSecurity WAF for additional layer (detection mode)
