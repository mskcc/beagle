# This tells the Makefile to read the file and export everything to the shell
-include .env.$(ENV)
export

# 1. Engine Detection
DOCKER_BIN := $(shell which podman 2> /dev/null || which docker 2> /dev/null)

# 2. Environment Setup (Defaults to dev)
ENV ?= dev

# Get the current branch name, replace slashes with underscores (Docker tags don't like slashes)
VERSION := $(shell git rev-parse --abbrev-ref HEAD | sed 's/\//_/g')

# 3. Pathing & Files
# We stack the Base file and the Environment-specific override file
COMPOSE_FILES := -f infra/compose/docker-compose.base.yml -f infra/compose/docker-compose.$(ENV).yml
ENV_FILE := .env.$(ENV)

# 4. Command Definition
# BEAGLE_VERSION is passed to satisfy the variable in docker-compose.base.yml
COMPOSE_CMD := BEAGLE_VERSION=$(VERSION) $(DOCKER_BIN) compose $(COMPOSE_FILES) --project-directory . --env-file $(ENV_FILE)

.PHONY: up down restart logs shell migrate clean build

# Generic exec command: make ENV=dev exec CMD="env | grep BEAGLE"
exec:
	$(COMPOSE_CMD) exec api $(CMD)

# Build images (useful for dev after changing requirements.txt)
build:
	$(COMPOSE_CMD) build

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
	$(COMPOSE_CMD) exec api python3 manage.py shell

migrate:
	$(COMPOSE_CMD) exec api python3 manage.py migrate

# Clean up volumes (useful for resetting the DB)
clean:
	$(COMPOSE_CMD) down -v
