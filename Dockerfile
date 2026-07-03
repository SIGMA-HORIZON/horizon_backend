FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# FIX réseau APT
RUN echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99ipv4 \
 && echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/99retries \
 && sed -i 's|deb.debian.org|ftp.debian.org|g' /etc/apt/sources.list \
 && sed -i 's|security.debian.org|ftp.debian.org|g' /etc/apt/sources.list

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
 && rm -rf /var/lib/apt/lists/*