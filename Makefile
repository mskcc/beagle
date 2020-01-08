SHELL:=/bin/bash
UNAME:=$(shell uname)
CURDIR_BASE:=$(shell basename "$(CURDIR)")
export LOG_DIR_ABS:=$(shell python -c 'import os; print(os.path.realpath("logs"))')

# help message for instructions on how to use this Makefile
help:
	@echo "This is the Makefile for setting up Beagle" ; \
	echo "1. install dependencies in the current directory with: 'make install'" ; \
	echo "2. initialize the database with: 'make db-init'" ; \
	echo "3. initialize the Django database entries with: 'make django-init'" ; \
	echo "4. to run Beagle, first start Postgres, RabbitMQ, and Celery with: 'make start-services'" ; \
	echo "5. start the main Django development server with: 'make runserver' "

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
	bioconda::rabix-bunny=1.0.4
	pip install -r requirements-cli.txt
	pip install -r requirements.txt

# ~~~~~ Set Up Demo Postgres Database for Dev ~~~~~ #
export BEAGLE_DB_NAME=db
export BEAGLE_DB_USERNAME=$(shell whoami)
export BEAGLE_DB_PASSWORD=admin
export BEAGLE_DB_PORT:=65528
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

# interactive Postgres console
# use command `\dt` to show all tables
db-inter:
	psql -p "$(PGPORT)" -U "$(PGUSER)" -W "$(PGDATABASE)"


# ~~~~~~ Celery tasks & RabbitMQ setup ~~~~~ #
# !! need to start RabbitMQ before celery, and both before running Django app servers !!
# corresponds to ./conf/rabbitmq.conf ;
export RABBITMQ_CONFIG_FILE:=$(CURDIR)/conf/rabbitmq
# give the RabbitMQ node cluster a name based on current dir; hopefully different from other instances on same server
export RABBITMQ_NODENAME:=rabbit_$(CURDIR_BASE)
export RABBITMQ_NODE_IP_ADDRESS:=127.0.0.1
export RABBITMQ_NODE_PORT:=5670
export RABBITMQ_LOG_BASE:=$(LOG_DIR_ABS)
export RABBITMQ_LOGS:=rabbitmq.log
export RABBITMQ_PID_FILE:=$(RABBITMQ_LOG_BASE)/rabbitmq.pid

export CELERY_BEAT_PID_FILE:=$(LOG_DIR_ABS)/celery.beat.pid
export CELERY_BEAT_LOGFILE:=$(LOG_DIR_ABS)/celery.beat.log
export CELERY_BEAT_SCHEDULE:=$(LOG_DIR_ABS)/celerybeat-schedule
export CELERY_WORKER_PID_FILE:=$(LOG_DIR_ABS)/celery.worker.pid
export CELERY_WORKER_LOGFILE:=$(LOG_DIR_ABS)/celery.worker.log
export CELERY_WORKER_JOB_SCHEDULER_PID_FILE:=$(LOG_DIR_ABS)/celery.worker.beagle_job_scheduler.pid
export CELERY_WORKER_JOB_SCHEDULER_LOGFILE:=$(LOG_DIR_ABS)/celery.worker.beagle_job_scheduler.log
export CELERY_WORKER_RUNNER_PID_FILE:=$(LOG_DIR_ABS)/celery.worker.runner.pid
export CELERY_WORKER_RUNNER_LOGFILE:=$(LOG_DIR_ABS)/celery.worker.runner.log
export CELERY_BROKER_URL:=amqp://$(RABBITMQ_NODE_IP_ADDRESS):$(RABBITMQ_NODE_PORT)

# these environment variables are required for IGO LIMS access by Beagle (values not included here):
# export BEAGLE_LIMS_USERNAME=some_username
# export BEAGLE_LIMS_PASSWORD=some_password


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

# start all of the Celery worker processes
celery-start:
	celery -A beagle_etl worker \
	-l info \
	--pidfile "$(CELERY_WORKER_PID_FILE)" \
	--logfile "$(CELERY_WORKER_LOGFILE)" \
	--detach && \
	celery -A beagle_etl beat \
	-l info \
	--pidfile "$(CELERY_BEAT_PID_FILE)" \
	--logfile "$(CELERY_BEAT_LOGFILE)" \
	--schedule "$(CELERY_BEAT_SCHEDULE)" \
	--detach && \
	celery -A beagle_etl worker \
	--concurrency 1 \
	-l info \
	-Q beagle_job_scheduler \
	--pidfile "$(CELERY_WORKER_JOB_SCHEDULER_PID_FILE)" \
	--logfile "$(CELERY_WORKER_JOB_SCHEDULER_LOGFILE)" \
	--detach && \
	celery -A beagle_etl worker \
	-l info \
	-Q runner_queue \
	--pidfile "$(CELERY_WORKER_RUNNER_PID_FILE)" \
	--logfile "$(CELERY_WORKER_RUNNER_LOGFILE)" \
	--detach

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
start-services:
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
# address to dev Ridgeback instance:
export DJANGO_RIDGEBACK_IP:=localhost
export DJANGO_RIDGEBACK_PORT:=7001

export BEAGLE_AUTH_LDAP_SERVER_URI=ldap_url_goes_here
export BEAGLE_LIMS_URL=beagle_lims_url_goes_here
export BEAGLE_RABIX_PATH=$(CURDIR)/conda/bin/rabix
export BEAGLE_IMPORT_FILE_GROUP=1a1b29cf-3bc2-4f6c-b376-d4c5d701166a
# export BEAGLE_RIDGEBACK_URL=http://silo:5003
export BEAGLE_RIDGEBACK_URL=http://$(DJANGO_RIDGEBACK_IP):$(DJANGO_RIDGEBACK_PORT)
export DJ_DEBUG_LOG:=$(LOG_DIR_ABS)/dj.debug.log

# initialize the Django app in the database
# do this after setting up the db above
django-init:
	python manage.py makemigrations
	python manage.py migrate
	python manage.py createsuperuser
	python manage.py loaddata file_system/fixtures/*
	python manage.py loaddata runner/fixtures/*
	python manage.py loaddata beagle_etl/fixtures/*


# start the Django development server
runserver:
	python manage.py runserver "$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)"

# start interactive bash with environment configured
bash:
	bash

# use the Django server superuser credentials to generate an authentication token
# fill this in with whatever values you used for a Django superuser account (above)
export USERNAME:=django_admin123
export PASSWORD:=1234
auth:
	curl -X POST \
	--header "Content-Type: application/json" \
	--data '{"username":"$(USERNAME)","password":"$(PASSWORD)"}' \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/api-token-auth/

# example request ID to use for testing LIMS request import
REQID:=07264_G
# fill this in with the token that was generated with `auth` above
TOKEN:=IUzI1NiJ9.eyJ0
import:
	curl -H "Content-Type: application/json" \
	-X POST \
	-H "Authorization: Bearer $(TOKEN)" \
	--data '{"request_ids":["$(REQID)"]}' \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/etl/import-requests/

request:
	curl -H "Content-Type: application/json" \
	-X GET \
	-H "Authorization: Bearer $(TOKEN)" \
	http://$(DJANGO_BEAGLE_IP):$(DJANGO_BEAGLE_PORT)/v0/fs/files/$(REQID)/

# check if the ports needed for services and servers are already in use on this system
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
port-check:
	ss -lntup | grep ':$(PORT)'
