FROM python:3.10-slim

LABEL maintainer="Nikhil Kumar (kumarn1@mskcc.org)" \
      version.image="1.0.0" \
      source.ridgeback="https://github.com/mskcc/beagle"

ENV DEBIAN_FRONTEND noninteractive
ENV PIP_ROOT_USER_ACTION ignore
ENV PIP_BREAK_SYSTEM_PACKAGES 1
ENV BEAGLE_BRANCH feature/IRIS_update

RUN apt-get update \
     # Install dependencies
        && apt-get -y --no-install-recommends install \
            wget curl libldap2-dev libsasl2-dev procps libssl-dev libxml2-dev libxslt-dev \
            libpq-dev gawk nodejs git nginx build-essential \
     # Install Beagle
        && cd /usr/bin \
        && git clone https://github.com/mskcc/beagle --branch $BEAGLE_BRANCH \
        && cd /usr/bin/beagle \
     # Install python packages
        && pip3 install --upgrade pip \
        && pip3 install --use-pep517 python-ldap \
        && pip3 install --use-pep517 -r requirements.txt \
    # Clean up image
        && apt-get -y purge --auto-remove build-essential \
        && rm -rf /var/lib/apt/lists/*


