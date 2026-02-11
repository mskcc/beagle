# 1. Engine Detection
DOCKER_BIN := $(shell which podman 2> /dev/null || which docker 2> /dev/null)

# 2. Command Definition
# --project-directory . ensures we look for Dockerfile and src/ in the root
# --env-file .env.dev ensures variables are available for both Compose and the Container
COMPOSE_DEV := $(DOCKER_BIN) compose -f infra/compose/docker-compose.dev.yml --project-directory . --env-file .env.dev

.PHONY: up down restart logs shell migrate

up:
	$(COMPOSE_DEV) up -d

down:
	$(COMPOSE_DEV) down

restart:
	$(COMPOSE_DEV) restart

logs:
	$(COMPOSE_DEV) logs -f

# Use 'src/manage.py' because that is the new location
shell:
	$(COMPOSE_DEV) exec api python manage.py shell

migrate:
	$(COMPOSE_DEV) exec api python manage.py migrate

# Clean up volumes (useful for resetting the DB)
clean:
	$(COMPOSE_DEV) down -v
