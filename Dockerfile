FROM python:3.10-slim

LABEL org.opencontainers.image.vendor="MSKCC" \
      org.opencontainers.image.authors="Nikhil Kumar (kumarn1@mskcc.org)" \
      org.opencontainers.image.created="2025-09-15T16:04:00Z" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.source="https://github.com/mskcc/beagle" \
      org.opencontainers.image.title="Beagle" \
      org.opencontainers.image.description="API for managing files, pipelines and runs."

ENV DEBIAN_FRONTEND noninteractive
ENV PIP_ROOT_USER_ACTION ignore
ENV PIP_BREAK_SYSTEM_PACKAGES 1
COPY requirements.txt /app/data/requirements.txt

RUN apt-get update \
     # Install dependencies
        && apt-get -y --no-install-recommends install \
            wget curl libldap2-dev libsasl2-dev procps libssl-dev libxml2-dev libxslt-dev \
            libpq-dev gawk nodejs git nginx build-essential \
     # Install python packages
        && pip3 install --upgrade pip \
        && pip3 install --use-pep517 python-ldap \
        && pip3 install --use-pep517 -r /app/data/requirements.txt \
    # Clean up image
        && apt-get -y purge --auto-remove build-essential \
        && apt-get -y --no-install-recommends install openssh-client \
        && rm -rf /var/lib/apt/lists/*


