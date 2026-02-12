FROM python:3.10-slim

LABEL org.opencontainers.image.vendor="MSKCC" \
      org.opencontainers.image.authors="Nikhil Kumar (kumarn1@mskcc.org)" \
      org.opencontainers.image.authors="C. Allan Bolipata (bolipatc@mskcc.org)" \
      org.opencontainers.image.created="2025-09-15T16:04:00Z" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.source="https://github.com/mskcc/beagle" \
      org.opencontainers.image.title="Beagle" \
      org.opencontainers.image.description="API for managing files, pipelines and runs."

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_ROOT_USER_ACTION=ignore \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 1. Install System Dependencies
# Added 'netcat-openbsd' for the entrypoint wait-for-db logic
RUN apt-get update && apt-get -y --no-install-recommends install \
    wget curl libldap2-dev libsasl2-dev procps libssl-dev libxml2-dev libxslt-dev \
    libpq-dev gawk nodejs git nginx build-essential netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# 2. Python Requirements
COPY requirements.txt /app/
RUN pip3 install --upgrade pip \
    && pip3 install --use-pep517 python-ldap \
    && pip3 install --use-pep517 -r /app/requirements.txt \
    && apt-get -y purge --auto-remove build-essential

# 3. Code & Entrypoint Setup
COPY src/ /app/src/
COPY infra/bin/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# This directory ensures 'python3 manage.py' commands from the Makefile work immediately
WORKDIR /app/src

EXPOSE 8000

# 4. The Bridge: Entrypoint + Default Command
# Entrypoint handles migrations/waiting; CMD handles starting the server
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Default command for Staging/Prod. (Dev overrides this in dev.yml)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "beagle.wsgi:application"]
