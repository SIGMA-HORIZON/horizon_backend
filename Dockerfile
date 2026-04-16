FROM python:3.12-slim

# Métadonnées
LABEL maintainer="SIGMA/ENSPY" \
      description="Horizon API — Portail Cloud Privé Proxmox"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python (couche cachée séparément)
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Code applicatif
COPY alembic.ini .
COPY horizon ./horizon
COPY scripts ./scripts

RUN chmod +x /app/scripts/docker-entrypoint.sh

# Utilisateur non-root pour la sécurité
RUN groupadd -r horizon && useradd -r -g horizon horizon
RUN chown -R horizon:horizon /app
USER horizon

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD sh -c 'curl -f "http://127.0.0.1:${PORT:-8000}/health" || exit 1'

CMD ["/app/scripts/docker-entrypoint.sh"]
