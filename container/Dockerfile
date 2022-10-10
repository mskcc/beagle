FROM postgres:14.5

LABEL maintainer="Nikhil Kumar {kumarn1@mskcc.org}" \
      version.image="1.0.0" \
      version.beagle="1.67.2" \
      source.beagle="https://github.com/mskcc/beagle"

ENV DEBIAN_FRONTEND=noninteractive
ENV ENVIRONMENT=dev
ENV BEAGLE_DB_NAME=db
ENV BEAGLE_DB_USERNAME=admin
ENV BEAGLE_DB_PASSWORD=correctHorseBatteryStaple
ENV BEAGLE_DB_PORT=5432
ENV BEAGLE_DB_URL=0.0.0.0
ENV PGLOG=postgres.log
ENV PGPORT=${BEAGLE_DB_PORT}
ENV POSTGRES_HOST_AUTH_METHOD=trust

RUN apt-get clean \ 
    && apt-get update -qq \
    && apt-get -y install \
        python python-dev python3 python3-pip wget \
        libldap2-dev libsasl2-dev libssl-dev \
        libpq-dev \
        gawk build-essential vim \
        git \
        default-jdk \
        procps \
    && cd /usr/bin \
    && git clone https://github.com/mskcc/beagle --branch develop \
    && cd /usr/bin/beagle \
    && python3 -m pip install python-ldap \
    && python3 -m pip install -r requirements.txt \
    && set -x\
    && mkdir -p /var/lib/postgresql/data \
    && chmod 775 /var/lib/postgresql \
    && chown postgres /var/lib/postgresql \
    && chown postgres /usr/bin/beagle \
    && chmod 775 -R /usr/bin/beagle

USER postgres
RUN mkdir -p /usr/bin/beagle/static \
    && pg_ctl -D /var/lib/postgresql/data initdb \
	&& pg_ctl -D /var/lib/postgresql/data -l /var/lib/postgresql/log start \
    && unset PGUSER \
    && unset PGPASSWORD \
    && createdb db \
    && createuser -s -i -d -r -l -w ${BEAGLE_DB_USERNAME} \
    && psql -c "ALTER ROLE ${BEAGLE_DB_USERNAME} WITH PASSWORD '${BEAGLE_DB_USERNAME}';" \
    && cd /usr/bin/beagle \
    && python3 manage.py makemigrations --merge \
    && python3 manage.py migrate \
	&& python3 manage.py collectstatic \
	&& echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('${BEAGLE_DB_USERNAME}', '', '${BEAGLE_DB_PASSWORD}')" | python3 manage.py shell \
	&& python3 manage.py loaddata \
    runner/tests/operator/cmo_ch/v2_1_0/qc/0a3c70a9-cf89-466b-bd39-4f409c21fb41.files.json \
    runner/tests/operator/cmo_ch/v2_1_0/qc/0a3c70a9-cf89-466b-bd39-4f409c21fb41.port.input.json \
    runner/tests/operator/cmo_ch/v2_1_0/qc/0a3c70a9-cf89-466b-bd39-4f409c21fb41.port.output.json \
    runner/tests/operator/cmo_ch/v2_1_0/qc/0a3c70a9-cf89-466b-bd39-4f409c21fb41.run.json \
    runner/tests/operator/cmo_ch/v2_1_0/qc/0a3c70a9-cf89-466b-bd39-4f409c21fb41.samples.json \
    runner/fixtures/runner.pipeline.json \
    runner/fixtures/runner.operator_run.json \
    file_system.sample.json \
    runner/fixtures/runner.run.json \
    file_system/fixtures/file_system.filegroup.json \
    file_system/fixtures/file_system.filetype.json \
    file_system/fixtures/file_system.storage.json \
    beagle_etl/fixtures/beagle_etl.operator.json \
    && echo "cd /usr/bin/beagle && pg_ctl -D /var/lib/postgresql/data -l /var/lib/postgresql/log start && gunicorn beagle.wsgi --log-file /usr/bin/beagle/log --bind 0.0.0.0:8081 --threads 10 --pythonpath /usr/bin/beagle" >> /usr/bin/beagle/start.sh \
    && chmod +x /usr/bin/beagle/start.sh


USER postgres


CMD ["/usr/bin/beagle/start.sh"]