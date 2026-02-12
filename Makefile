# This tells the Makefile to read the file and export everything to the shell
-include .env.$(ENV)
export

# 1. Engine Detection
DOCKER_BIN := $(shell which podman 2> /dev/null || which docker 2> /dev/null)

# 2. Environment Setup (Defaults to dev)
ENV ?= dev

# Get the current branch name, replace slashes with underscores (Docker tags don't like slashes)
VERSION := $(shell git rev-parse --abbrev-ref HEAD | sed 's/\//_/g')
# List the directories needed from your .env.dev

PREP_DIRS := infra/data/postgres infra/data/logs infra/data/beagle_dev_pgbouncer infra/data/beagle_dev_logrotate infra/data/beagle_dev_backup

# 3. Pathing & Files
# We stack the Base file and the Environment-specific override file
COMPOSE_FILES := -f infra/compose/docker-compose.base.yml -f infra/compose/docker-compose.$(ENV).yml
ENV_FILE := .env.$(ENV)

# 4. Command Definition
# Add -p beagle_$(ENV) to the command
COMPOSE_CMD := BEAGLE_VERSION=$(VERSION) $(DOCKER_BIN) compose \
    -p beagle_$(ENV) \
    $(COMPOSE_FILES) \
    --project-directory . \
    --env-file $(ENV_FILE)

.PHONY: up down restart logs shell migrate clean build

# Generic exec command: make ENV=dev exec CMD="env | grep BEAGLE"
exec:
	$(COMPOSE_CMD) exec api $(CMD)

# Build images (useful for dev after changing requirements.txt)
build:
	$(COMPOSE_CMD) build $(args)

prep:
	@mkdir -p $(PREP_DIRS)

up:
	$(COMPOSE_CMD) up -d

down:
	$(COMPOSE_CMD) down

restart:
	$(COMPOSE_CMD) restart

logs:
	$(COMPOSE_CMD) logs -f

# Note: working_dir is /app/src, so we call 'python3 manage.py'
shell:
	$(COMPOSE_CMD) exec beagle python3 manage.py shell

migrate:
	$(COMPOSE_CMD) exec beagle python3 manage.py migrate

# Clean up volumes (useful for resetting the DB)
clean:
	$(COMPOSE_CMD) down -v


# Start only the core infra
up-infra: prep
	$(COMPOSE_CMD) up -d --no-deps beagle_postgres beagle_rabbitmq beagle_pgbouncer

# Start only the Django API
up-beagle:
	$(COMPOSE_CMD) up -d --no-deps beagle

# Start only a specific worker (e.g., make worker name=beagle_celery_default_queue)
up-worker:
	$(COMPOSE_CMD) up -d --no-deps $(name)

# List containers for the CURRENT environment only
ps:
	@echo "--- Status for Project: beagle_$(ENV) ---"
	$(COMPOSE_CMD) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

# List ALL active compose projects on this machine
status:
	@echo "--- Active Compose Projects ---"
	$(DOCKER_BIN) compose ls
