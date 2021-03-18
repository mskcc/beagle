SHELL:=/bin/bash
UNAME:=$(shell uname)
CURDIR_BASE:=$(shell basename "$(CURDIR)")
export LOG_DIR_ABS:=$(shell python -c 'import os; print(os.path.realpath("logs"))')


define help
This is the Makefile for setting up Beagle development instance. It contains pre-configured environment variables and scripted recipes to help you get Beagle up and running easily.

Basic dev instance setup instructions:
-------------------------------------

1. install dependencies in the current directory with:
make install

2a. initialize the database with:
make db-init

- NOTE: you might need to adjust the PostgreSQL port variable BEAGLE_DB_PORT to avoid conflicts on a shared server

2b. run the test suite with:
make test

3. initialize the Django database and set a admin (superuser) account with:
make django-init

4. to run Beagle, first start Postgres, RabbitMQ, and Celery with:
make start-services

5. start the main Django development server with:
make runserver


Remember to export these environment variables for IGO LIMS access by Beagle before starting services and Django servers:

export BEAGLE_LIMS_USERNAME=some_username
export BEAGLE_LIMS_PASSWORD=some_password
export BEAGLE_LIMS_URL=beagle_lims_url_goes_here
export BEAGLE_AUTH_LDAP_SERVER_URI=ldap_url_goes_here

Demo Usage
----------

1. Generate an authentication token with the Django admin credentials you created:
make auth USERNAME=<admin_username> PASSWORD=<admin_password>

2. Test a database import from IGO LIMS by request ID:
make import REQID=07264_G TOKEN=<token from auth command>



Extras
------

- run the test suite:
make test

- Shutdown all services:
make stop-services

- Check if pre-configured ports are already occupied on your system:
make check-port-collision
make port-check PORT=<some_port>

- enter an interactive bash session with the environment variables pre-populated from this Makefile
make bash

- check if Postgres, Celery, and RabbitMQ are running:
make db-check
make celery-check
make rabbitmq-check

Consult the contents of this Makefile for other Beagle management recipes.

endef
export help
help:
	@printf "$$help"

.PHONY : help

# ~~~~~ Setup Conda ~~~~~ #
PATH:=$(CURDIR)/conda/bin:$(PATH)
unexport PYTHONPATH
unexport PYTHONHOME

# install versions of conda for Mac or Linux, Python 2 or 3
ifeq ($(UNAME), Darwin)
CONDASH:=Miniconda3-4.7.12.1-MacOSX-x86_64.sh
endif

ifeq ($(UNAME), Linux)
CONDASH:=Miniconda3-4.7.12.1-Linux-x86_64.sh
endif

CONDAURL:=https://repo.continuum.io/miniconda/$(CONDASH)
conda:
	@echo ">>> Setting up conda..."
	@wget "$(CONDAURL)" && \
	bash "$(CONDASH)" -b -p conda && \
	rm -f "$(CONDASH)"

# install the Beagle requirements
install: conda
	conda install -y \
	conda-forge::ncurses=6.1 \
	rabbitmq-server=3.7.16 \
	anaconda::postgresql=11.2 \
	conda-forge::python-ldap=3.2.0 \
	bioconda::rabix-bunny=1.0.4 \
	conda-forge::jq
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
# pip install git+https://github.com/mskcc/beagle_cli.git@develop
# pip install -r requirements-cli.txt # <- what happened to this file?

BEAGLE_BACKUP_DB_FOLDER=/juno/work/ci/beagle_backups/
export ENVIRONMENT=dev
# ~~~~~ Set Up Demo Postgres Database for Dev ~~~~~ #
export BEAGLE_DB_NAME=db
export BEAGLE_DB_USERNAME=$(shell whoami)
export BEAGLE_DB_PASSWORD=admin
export BEAGLE_DB_PORT:=65527
export BEAGLE_DB_URL:=localhost

export PGDATA=$(BEAGLE_DB_NAME)
export PGUSER=$(BEAGLE_DB_USERNAME)
export PGHOST=$(BEAGLE_DB_URL)
export PGLOG=$(LOG_DIR_ABS)/postgres.log
export PGPASSWORD=$(BEAGLE_DB_PASSWORD)
export PGDATABASE=$(BEAGLE_DB_NAME)
export PGPORT=$(BEAGLE_DB_PORT)
export TIMESTAMP_STR:=$(shell date '+%F_%T')
export DB_BACKUP_DIR:=$(CURDIR)/db_backup
export DB_BACKUP_FILE:=$(DB_BACKUP_DIR)/$(TIMESTAMP_STR)

# directory to hold the Postgres database files
$(PGDATA):
	mkdir -p "$(PGDATA)"

# dir to hold db backups
$(DB_BACKUP_DIR):
	mkdir -p "$(DB_BACKUP_DIR)"

# dir to hold server logs
$(LOG_DIR_ABS):
	mkdir -p "$(LOG_DIR_ABS)"

# set up & start the Postgres db server instance
db-init: $(PGDATA) $(LOG_DIR_ABS)
	set -x && \
	pg_ctl -D "$(PGDATA)" initdb && \
	pg_ctl -D "$(PGDATA)" -l "$(PGLOG)" start && \
	createdb

# start the Postgres database server process
db-start:
	pg_ctl -D "$(PGDATA)" -l "$(PGLOG)" start

# stop the db server
db-stop:
	pg_ctl -D "$(PGDATA)" stop

# check if db server is running
db-check:
	pg_ctl status

# make a Postgres db dump
db-backup: $(DB_BACKUP_DIR)
	pg_dump -d "$(PGDATABASE)" > "$(DB_BACKUP_FILE)"

# restore db from Postgres db dump; pass arg `DBFILE=some_file` to `make`
db-restore:
	@echo ">>> restoring db from DBFILE: $(DBFILE)"
	if [ -n "$(DBFILE)" ]; then \
	psql "$(PGDATABASE)" < "$(DBFILE)" ; fi

sync: 
	LATEST_DUMP=`ssh voyager ls -Art $(BEAGLE_BACKUP_DB_FOLDER) | tail -n 1` && \
	rsync --progress voyager:$(BEAGLE_BACKUP_DB_FOLDER)$$LATEST_DUMP . && \
	psql $(PGDATABASE) < $$LATEST_DUMP

# interactive Postgres console
# use command `\dt` to show all tables
db-inter:
	psql -p "$(PGPORT)" -U "$(PGUSER)" -W "$(PGDATABASE)"


# ~~~~~~ Celery tasks & RabbitMQ setup ~~~~~ #
# !! need to start RabbitMQ before celery, and both before running Django app servers !!
export BEAGLE_RABBITMQ_USERNAME:=guest
export BEAGLE_RABBITMQ_PASSWORD:=guest
export BEAGLE_RUNNER_QUEUE:=beagle_runner_queue
export BEAGLE_DEFAULT_QUEUE:=beagle_default_queue
export BEAGLE_JOB_SCHEDULER_QUEUE:=beagle_job_scheduler_queue
# these environment variables are required for IGO LIMS access by Beagle (values not included here):
# export BEAGLE_LIMS_USERNAME=some_username
# export BEAGLE_LIMS_PASSWORD=some_password
# export BEAGLE_AUTH_LDAP_SERVER_URI=ldap_url_goes_here
# export BEAGLE_LIMS_URL=beagle_lims_url_goes_here

# corresponds to ./conf/rabbitmq.conf ;
export RABBITMQ_CONFIG_FILE:=$(CURDIR)/conf/rabbitmq
# give the RabbitMQ node cluster a name based on current dir; hopefully different from other instances on same server
export RABBITMQ_NODENAME:=rabbit_$(CURDIR_BASE)
export RABBITMQ_NODE_IP_ADDRESS:=127.0.0.1
export RABBITMQ_NODE_PORT:=5679
export RABBITMQ_LOG_BASE:=$(LOG_DIR_ABS)
export RABBITMQ_LOGS:=rabbitmq.log
export RABBITMQ_PID_FILE:=$(RABBITMQ_LOG_BASE)/rabbitmq.pid
export RABBITMQ_USERNAME:=$(BEAGLE_RABBITMQ_USERNAME)
export RABBITMQ_PASSWORD:=$(BEAGLE_RABBITMQ_PASSWORD)
export BEAGLE_RABBITMQ_URL:=amqp://$(RABBITMQ_USERNAME):$(RABBITMQ_PASSWORD)@$(RABBITMQ_NODE_IP_ADDRESS):$(RABBITMQ_NODE_PORT)

export CELERY_BEAT_PID_FILE:=$(LOG_DIR_ABS)/celery.beat.pid
export CELERY_BEAT_LOGFILE:=$(LOG_DIR_ABS)/celery.beat.log
export CELERY_BEAT_SCHEDULE:=$(LOG_DIR_ABS)/celerybeat-schedule
export CELERY_WORKER_PID_FILE:=$(LOG_DIR_ABS)/celery.worker.pid
export CELERY_WORKER_LOGFILE:=$(LOG_DIR_ABS)/celery.worker.log
export CELERY_WORKER_JOB_SCHEDULER_PID_FILE:=$(LOG_DIR_ABS)/celery.worker.beagle_job_scheduler.pid
export CELERY_WORKER_JOB_SCHEDULER_LOGFILE:=$(LOG_DIR_ABS)/celery.worker.beagle_job_scheduler.log
export CELERY_WORKER_RUNNER_PID_FILE:=$(LOG_DIR_ABS)/celery.worker.runner.pid
export CELERY_WORKER_RUNNER_LOGFILE:=$(LOG_DIR_ABS)/celery.worker.runner.log
export CELERY_BROKER_URL:=$(BEAGLE_RABBITMQ_URL)

# check for the presence of extra required env variables
check-env:
	@for i in BEAGLE_LIMS_URL \
	BEAGLE_AUTH_LDAP_SERVER_URI \
	BEAGLE_LIMS_PASSWORD \
	BEAGLE_LIMS_USERNAME; do \
	[ -z "$$(printenv BEAGLE_LIMS_USERNAME)" ] && echo ">>> env variable $$i is not set; some features may not work" || : ; done

# start the RabbitMQ server in the background
rabbitmq-start: $(LOG_DIR_ABS)
	rabbitmq-server -detached

# start the RabbitMQ server in the foreground
rabbitmq-start-inter: $(LOG_DIR_ABS)
	rabbitmq-server

# stop the background RabbitMQ server process
rabbitmq-stop:
	rabbitmqctl stop

# check if RabbitMQ is running
rabbitmq-check:
	rabbitmqctl status
	ps auxww | grep rabbit | grep '$(CURDIR)'

# remove old RabbitMQ cluster configs;
# had to do this when RabbitMQ kept crashing due to not finding cluster https://stackoverflow.com/questions/6948624/mnesia-cant-connect-to-another-node
rabbitmq-clean:
	rm -rf $(CURDIR)/conda/var/lib/rabbitmq/mnesia/*
# ./conda/var/lib/rabbitmq/mnesia/rabbit_beagle/cluster_nodes.config
# ./conda/var/lib/rabbitmq/mnesia/rabbit/cluster_nodes.config

# start all of the Celery worker processes in the background
celery-start:
	celery -A beagle_etl worker \
	-l info \
	-Q "$(BEAGLE_DEFAULT_QUEUE)" \
	--pidfile "$(CELERY_WORKER_PID_FILE)" \
	--logfile "$(CELERY_WORKER_LOGFILE)" &
	celery -A beagle_etl beat \
	-l info \
	--pidfile "$(CELERY_BEAT_PID_FILE)" \
	--logfile "$(CELERY_BEAT_LOGFILE)" \
	--schedule "$(CELERY_BEAT_SCHEDULE)" &
	celery -A beagle_etl worker \
	--concurrency 1 \
	-l info \
	-Q "$(BEAGLE_JOB_SCHEDULER_QUEUE)" \
	--pidfile "$(CELERY_WORKER_JOB_SCHEDULER_PID_FILE)" \
	--logfile "$(CELERY_WORKER_JOB_SCHEDULER_LOGFILE)" &
	celery -A beagle_etl worker \
	-l info \
	-Q "$(BEAGLE_RUNNER_QUEUE)" \
	--pidfile "$(CELERY_WORKER_RUNNER_PID_FILE)" \
	--logfile "$(CELERY_WORKER_RUNNER_LOGFILE)" &

flower:
	flower -A beagle_etl --port=5555 -logLevel=debug --broker=$(CELERY_BROKER_URL)
# check that the Celery processes are running
celery-check:
	-ps auxww | grep 'celery' | grep -v 'grep' | grep -v 'make' | grep '$(CURDIR)'

# kill all the Celery processes started from this dir
celery-stop:
	ps auxww | grep 'celery' | grep -v 'grep' | grep -v 'make' | grep '$(CURDIR)' | awk '{print $$2}' | xargs kill -9
# also can use the PID files:
# head -1 "$(CELERY_WORKER_PID_FILE)" | xargs kill -9
# head -1 "$(CELERY_BEAT_PID_FILE)" | xargs kill -9
# head -1 "$(CELERY_WORKER_JOB_SCHEDULER_PID_FILE)" | xargs kill -9
# head -1 "$(CELERY_WORKER_RUNNER_PID_FILE)" | xargs kill -9

# shortcut to start all the services in the proper order
start-services: check-env
	-$(MAKE) db-start || echo ">>> Could not start database server; is it already running?"
	$(MAKE) rabbitmq-start
	$(MAKE) celery-start

stop-services:
	$(MAKE) celery-stop
	$(MAKE) rabbitmq-stop
	$(MAKE) db-stop



# ~~~~~ Set Up Django ~~~~~ #
export DJANGO_BEAGLE_IP:=localhost
export DJANGO_BEAGLE_PORT:=6991
export BEAGLE_URL:=http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)
export BEAGLE_ENDPOINT:=$(BEAGLE_URL)
export BEAGLE_RABIX_PATH=$(CURDIR)/conda/bin/rabix
export BEAGLE_IMPORT_FILE_GROUP=1a1b29cf-3bc2-4f6c-b376-d4c5d701166a

# address to dev Ridgeback instance;
# http://silo:5003 by default
export DJANGO_RIDGEBACK_IP:=localhost
export DJANGO_RIDGEBACK_PORT:=7001
export BEAGLE_RIDGEBACK_URL=http://$(DJANGO_RIDGEBACK_IP):$(DJANGO_RIDGEBACK_PORT)
export DJ_DEBUG_LOG:=$(LOG_DIR_ABS)/dj.debug.log


# initialize the Django app in the database
# do this after setting up the db above
django-init:
	if [ ! -d "static" ]; then mkdir static; fi
	python manage.py makemigrations --merge
	python manage.py migrate
	python manage.py collectstatic
	python manage.py createsuperuser
	python manage.py loaddata \
	beagle_etl.operator.json \
	file_system.filegroup.json \
	file_system.filetype.json \
	file_system.storage.json \
	runner.pipeline.json

TEST_ARGS?=
test: check-env
	python manage.py test $(TEST_ARGS)

# this one needs external LIMS access currently and takes a while to run so dont include it by default
test-lims: check-env
	python manage.py test \
	beagle_etl.tests.jobs.test_lims_etl_jobs

# start the Django development server
runserver: check-env
	python manage.py runserver $(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)

MIGRATION_ARGS?=
migrate: check-env
	python manage.py migrate $(MIGRATION_ARGS)
shell : check-env
	python manage.py shell_plus --print-sql


dumpdata: check-env
	python manage.py dumpdata

makemigrations: check-env
	python manage.py makemigrations

# start interactive bash with environment configured
bash:
	bash

# use the Django server superuser credentials to generate an authentication token
# fill this in with whatever values you used for a Django superuser account (above)
# save the credentials into a file
export USERNAME:=
export PASSWORD:=
export AUTH_FILE:=$(shell echo $$HOME)/.$(CURDIR_BASE).json
auth:
	@[ -z "$(USERNAME)" ] && echo ">>> ERROR: USERNAME must be supplied; make auth USERNAME=foo PASSWORD=bar" && exit 1 || :
	@[ -z "$(PASSWORD)" ] && echo ">>> ERROR: PASSWORD must be suppled; make auth USERNAME=foo PASSWORD=bar" && exit 1 || :
	@token=$$(curl --silent -X POST --header "Content-Type: application/json" --data '{"username":"$(USERNAME)","password":"$(PASSWORD)"}' http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/api-token-auth/ | jq --exit-status -r '.access' ) ; \
	[ -z "$${token}" ] && echo ">>> ERROR: 'token' returned by server is zero length; did you provide the correct credentials?" && exit 1 || : ; \
	[ "$${token}" == "null" ] && echo ">>> ERROR: 'token' returned by the server is 'null'; did you provide the correct crendentials?" && exit 1 || : ; \
	jq -n --arg token "$$token" '{"token":$$token}' > "$(AUTH_FILE)" && \
	echo ">>> authentication token stored in file: $(AUTH_FILE)"

# generate the
$(AUTH_FILE):
	$(MAKE) auth

# example request ID to use for testing LIMS request import
REQID:=07264_G
# fill this in with the token that was generated with `auth` above
TOKEN:=IUzI1NiJ9.eyJ0
# import files data about samples in a request from the IGO LIMS
import:
	curl -H "Content-Type: application/json" \
	-X POST \
	-H "Authorization: Bearer $(TOKEN)" \
	--data '{"request_ids":["$(REQID)"]}' \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/etl/import-requests/


# create a dev instance of the Argos pipeline
DEVNAME:=argos-dev
DEVURL:=https://github.com/mskcc/argos-cwl
DEVVER:=1.0.0-rc5
DEVENTRY:=workflows/pair-workflow-sv.cwl
DEVOUTPUT:=$(CURDIR)/output/argos-dev
DEVGROUP:=1a1b29cf-3bc2-4f6c-b376-d4c5d701166a

$(DEVOUTPUT):
	mkdir -p "$(DEVOUTPUT)"

get-pipelines:
	curl --silent -H "Content-Type: application/json" \
	-X GET \
	-H "Authorization: Bearer $(TOKEN)" \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/run/pipelines/ | jq

check-dev-pipeline-registered: $(AUTH_FILE)
	@echo ">>> checking if the dev pipeline is already registered in the Beagle database..." ; \
	token=$$( jq -r '.token' "$(AUTH_FILE)" ) && \
	curl --silent -H "Content-Type: application/json" \
	-X GET \
	-H "Authorization: Bearer $$token" \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/run/pipelines/ | \
	jq --exit-status '.results | .[] | select(.name | contains("$(DEVNAME)"))' > /dev/null

register-dev-pipeline: $(DEVOUTPUT) $(AUTH_FILE)
	@echo ">>> trying to register the dev pipeline in the Beagle database..." ; \
	token=$$( jq -r '.token' "$(AUTH_FILE)" ) && \
	$(MAKE) check-dev-pipeline-registered && \
	echo ">>> dev pipeline $(DEVNAME) already exists in the Beagle database" || \
	{ echo ">>> registering dev pipeline $(DEVNAME) in Beagle database" ; \
	curl -H "Content-Type: application/json" \
	-X POST \
	-H "Authorization: Bearer $$token" \
	-d '{ "name": "$(DEVNAME)", "github": "$(DEVURL)", "version": "$(DEVVER)", "entrypoint": "$(DEVENTRY)", "output_file_group": "$(DEVGROUP)", "output_directory": "$(DEVOUTPUT)"}' \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/run/pipelines/ ; }

# get info about the files and samples in a request, from the Beagle API
files-request:
	curl -H "Content-Type: application/json" \
	-X GET \
	-H "Authorization: Bearer $(TOKEN)" \
	--data '{"request_ids":["$(REQID)"]}' \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/fs/files/
# python ./beagle_cli.py files list --metadata='requestId:$(REQID)'

# get info on a single file
REQFILE:=b37.fasta
file-get:
	curl -H "Content-Type: application/json" \
	-X GET \
	-H "Authorization: Bearer $(TOKEN)" \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/fs/files/?filename=$(REQFILE)

# start a Argos run for a given request in the Beagle db
run-request:
	curl -H "Content-Type: application/json" \
	-X POST \
	-H "Authorization: Bearer $(TOKEN)" \
	--data '{"request_ids":["$(REQID)"], "pipeline_name": "argos"}' \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/run/request/

# send a pipeline input to the API to start running
REQJSON:=fixtures/tests/run_argos.json
run-request-api: $(AUTH_FILE)
	@token=$$( jq -r '.token' "$(AUTH_FILE)" ) && \
	curl -H "Content-Type: application/json" \
	-X POST \
	-H "Authorization: Bearer $$token" \
	--data @$(REQJSON) \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/run/api/

# make a demo Argos input.json file from the template fixture;
# need to update the fixture with the app ID of the demo pipeline that was loaded in the database
INPUT_TEMPLATE:=fixtures/tests/juno_argos_demo2.pipeline_input.json
DEMO_INPUT:=input.json
$(DEMO_INPUT): $(INPUT_TEMPLATE) $(AUTH_FILE)
	@token=$$( jq -r '.token' "$(AUTH_FILE)" ) && \
	$(MAKE) check-dev-pipeline-registered && \
	{ \
	appid=$$(curl --silent -H "Content-Type: application/json" -X GET -H "Authorization: Bearer $$token" http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/run/pipelines/ | jq -r --exit-status '.results | .[] | select(.name | contains("$(DEVNAME)")) | .id' ) && \
	jq --arg appid "$$appid" '.app = $$appid' fixtures/tests/juno_argos_demo2.pipeline_input.json > $(DEMO_INPUT) ; \
	} || { echo ">>> input didnt work" ; exit 1; }
.PHONY: $(DEMO_INPUT)

# submit a demo Argos run using the dev Argos pipeline entry in the database
demo-run: register-dev-pipeline $(DEMO_INPUT)
	@python manage.py loaddata fixtures/tests/juno_argos_demo2.file.json
	@python manage.py loaddata fixtures/tests/juno_argos_demo2.filemetadata.json
	@python manage.py loaddata fixtures/tests/argos_reference_files.json
	@$(MAKE) run-request-api REQID=DemoRequest1 REQJSON=$(DEMO_INPUT)

# check if the ports needed for services and servers are already in use on this system
ifeq ($(UNAME), Darwin)
# On macOS High Sierra, use this command: lsof -nP -i4TCP:$PORT | grep LISTEN
check-port-collision:
	@for i in \
	"DJANGO_BEAGLE_PORT:$(DJANGO_BEAGLE_PORT)" \
	"BEAGLE_DB_PORT:$(BEAGLE_DB_PORT)" \
	"RABBITMQ_NODE_PORT:$(RABBITMQ_NODE_PORT)" \
	"DJANGO_RIDGEBACK_PORT:$(DJANGO_RIDGEBACK_PORT)" \
	"PGPORT:$(PGPORT)" ; do ( \
	label="$$(echo $$i | cut -d ':' -f1)" ; \
	port="$$(echo $$i | cut -d ':' -f2)" ; \
	lsof -ni | grep LISTEN | tr -s ' ' | cut -d ' ' -f9 | sed -e 's|.*:\([0-9]*\)$$|\1|g' | sort -u | grep -qw "$$port" && echo ">>> $$label port has a collision; something is already running on port $$port" || : ; \
	) ; done

port-check:
	lsof -i:$(DJANGO_BEAGLE_PORT),$(BEAGLE_DB_PORT),$(RABBITMQ_NODE_PORT),$(DJANGO_RIDGEBACK_PORT),$(PGPORT) | \
	grep LISTEN
endif

ifeq ($(UNAME), Linux)
check-port-collision:
	@for i in \
	"DJANGO_BEAGLE_PORT:$(DJANGO_BEAGLE_PORT)" \
	"BEAGLE_DB_PORT:$(BEAGLE_DB_PORT)" \
	"RABBITMQ_NODE_PORT:$(RABBITMQ_NODE_PORT)" \
	"DJANGO_RIDGEBACK_PORT:$(DJANGO_RIDGEBACK_PORT)" \
	"PGPORT:$(PGPORT)" ; do ( \
	label="$$(echo $$i | cut -d ':' -f1)" ; \
	port="$$(echo $$i | cut -d ':' -f2)" ; \
	ss -lntu | tr -s ' ' | cut -d ' ' -f5 | sed -e 's|.*:\([0-9]*$$\)|\1|g' | sort -u | grep -qw "$$port" && echo ">>> $$label port has a collision; something is already running on port $$port" || : ; \
	) ; done
PORT=
# check if a port is already in use on the system
port-check:
	ss -lntup | grep ':$(PORT)'
endif
