---
name: docker
description: >
  Guía para Docker. Dockerfile, images, containers, multi-stage builds.
  Trigger: Cuando se modifica Dockerfile, .dockerignore o se configura containerización.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Proyecto tiene Dockerfile
- Se configura containerización
- Troubleshooting de builds o containers
- Optimización de imagen

## Dockerfile de Este Proyecto

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (if needed)
# EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
```

## Multi-Stage Build (Optimizado)

```dockerfile
# Stage 1: Build
FROM python:3.12-slim as builder
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY . .
CMD ["python", "main.py"]
```

## Common Commands

```bash
# Build image
docker build -t flux-cost-bot .

# Run container
docker run -d --name flux-bot \
  -e TELEGRAM_BOT_TOKEN=xxx \
  -e GOOGLE_API_KEY=xxx \
  -e ADMIN_CHAT_ID=xxx \
  flux-cost-bot

# Run con volumen (dev)
docker run -v $(pwd):/app -it flux-bot bash

# Logs
docker logs -f flux-bot

# Exec into container
docker exec -it flux-bot bash

# Build multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t mybot .
```

## .dockerignore

```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
.venv/
.git/
.gitignore
*.md
.DS_Store
*.log
.env
!/.env.example
service_account.json
```

## Python Docker Tips

1. **Usar slim images** → Menos peso
2. **Orden de capas** → Requerimientos primero (cache)
3. **--no-cache-dir en pip** → Menos tamaño
4. **No copy todo** → Usar .dockerignore
5. **Usuario no-root** → Seguridad

## Security

```dockerfile
# Create non-root user
RUN addgroup -g 1000 appgroup && \
    adduser -u 1000 -G appgroup -D appuser

USER appuser
```

## Resources

- **Docs**: https://docs.docker.com/
- **Python images**: https://hub.docker.com/_/python
- **Best practices**: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
