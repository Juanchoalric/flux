---
name: fly-io
description: >
  Guía para Fly.io. Deployment, volumes, secrets, auto-scaling.
  Trigger: Cuando se modifica fly.toml o se deploya a producción.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Proyecto usa Fly.io para hosting
- Se configuran secrets, volumes, o scaling
- Troubleshooting de deployment
- Configuración de región

## Setup

```bash
# Install flyctl
brew install flyctl

# Login
fly auth login

# Init (si no hay fly.toml)
fly launch
```

## fly.toml de Este Proyecto

```toml
app = "flux-cost-bot"
primary_region = "eze"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8080
  force_https = true
  min_machines_running = 1
```

## Secrets (Environment Variables)

```bash
# Set secrets
fly secrets set TELEGRAM_BOT_TOKEN=xxx
fly secrets set GOOGLE_API_KEY=xxx
fly secrets set ADMIN_CHAT_ID=xxx

# List secrets
fly secrets list

# Remove secret
fly secrets unset TELEGRAM_BOT_TOKEN
```

## Machine Configuration

```toml
[http_service]
  internal_port = 8080
  force_https = true
  min_machines_running = 1  # Keep at least 1 running
  max_machines_running = 3  # Auto-scale up to 3

[[vm]]
  size = "shared-cpu-1x"   # or "dedicated-1x", "performance-1x"
  cpu_kind = "shared"       # or "dedicated"
  cpus = 1
  memory_mb = 256
```

## Volumes (Persistent Storage)

```bash
# Create volume
fly volumes create flux_data --size 1 --region eze

# Mount in fly.toml
[mounts]
  source = "flux_data"
  destination = "/app/data"
```

## Deploy

```bash
# Deploy
fly deploy

# Deploy with specific dockerfile
fly deploy -d Dockerfile.production

# Deploy to specific region
fly deploy --region eze

# Scale horizontally
fly scale count 3

# Scale vertically
fly scale vm dedicated-cpu-2x
```

## Logs & Monitoring

```bash
# View logs
fly logs

# Stream logs
fly logs -f

# Status
fly status

# Restart machine
fly machine restart <machine-id>
```

## Health Checks

```toml
[[http_service.checks]]
  path = "/health"
  interval = "30s"
  timeout = "5s"
  grace_period = "10s"
```

## Common Commands

```bash
# SSH into machine
fly ssh console

# Copy file
fly ssh sftp get /app/logs/bot.log ./bot.log

# Restart app
fly apps restart flux-cost-bot

# Destroy app
fly apps destroy flux-cost-bot
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check Dockerfile + requirements.txt |
| App won't start | `fly logs` to see errors |
| Out of memory | Scale VM size with `fly scale vm` |
| Region latency | Choose region closest to users |
| Secret not found | `fly secrets list` to verify |

## Resources

- **Docs**: https://fly.io/docs/
- **CLI reference**: https://fly.io/docs/flyctl/
- **Pricing**: https://fly.io/docs/about/pricing/
- **Machines**: https://fly.io/docs/machines/
