FROM ubuntu:19.10

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get clean && apt-get update -qq \
    && apt-get -y install \
        python python-pip python-dev python3 python3-pip wget \
        libldap2-dev libsasl2-dev libssl-dev \
        gawk build-essential \
        git

RUN python3 -m pip install --upgrade pip python-ldap

RUN apt-get update -qq && apt-get -y install postgresql postgresql-contrib libpq-dev

RUN cd /tmp \
    && git clone https://github.com/mskcc/beagle \
    && cd beagle \
    && pip3 install -r requirements.txt
