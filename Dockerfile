FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# =========================
# FIX stabilité APT (réseau + Debian)
# =========================
RUN set -eux; \
    echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99ipv4; \
    echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/99retries; \
    \
    # sécurise sources Debian (bookworm / trixie / variantes)
    if [ -f /etc/apt/sources.list ]; then \
        sed -i 's|deb.debian.org|ftp.debian.org|g' /etc/apt/sources.list; \
        sed -i 's|security.debian.org|ftp.debian.org|g' /etc/apt/sources.list; \
    fi; \
    \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        curl; \
    rm -rf /var/lib/apt/lists/*

# =========================
# Dépendances Python
# =========================
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# =========================
# Code
# =========================
COPY alembic.ini .
COPY horizon ./horizon
COPY scripts ./scripts

RUN chmod +x /app/scripts/docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD sh -c 'curl -f "http://127.0.0.1:${PORT:-8000}/health" || exit 1'

CMD ["/app/scripts/docker-entrypoint.sh"]