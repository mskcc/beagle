FROM ubuntu:19.10

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get clean && apt-get update -qq \
    && apt-get -y install \
        python python-pip python-dev python3 python3-pip wget \
        libldap2-dev libsasl2-dev libssl-dev \
        postgresql postgresql-contrib libpq-dev \
        gawk build-essential \
        git \
    && python3 -m pip install --upgrade pip python-ldap

RUN cd /usr/bin \
    && git clone https://github.com/mskcc/beagle \
    && cd beagle \
    && pip3 install -r requirements.txt
