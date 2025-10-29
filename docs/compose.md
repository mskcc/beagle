# Beagle Compose File – `compose.yaml`

The Docker‑Compose file defines the entire runtime environment for **Beagle**, including databases, message queues, workers, and auxiliary services such as log rotation and backups.

> **Tip** – All environment variables are sourced from the `.env` file in the project root. Replace placeholders (`${VAR}`) with your own values or export them before running `docker compose up`.

---

## 1. Global Settings

| Key | Purpose |
|-----|---------|
| `name` | Name of the stack (`Beagle Services ${BEAGLE_DEPLOYMENT}`) |
| `x-beagle_celery` | Anchor definition for all Celery worker services (image, user, networking, env_file, volumes, etc.) |

---

## 2. Services

| Service | Description |
|---------|-------------|
| **`beagle_create_volumes`** | Initializes and sets ownership of all data volumes (Postgres, Pgbouncer, logs, celery, rabbitmq, server, logrotate, db_backup). |
| **`beagle_postgres`** | PostgreSQL 17‑trixie instance. Uses a custom `postgres/` volume for persistence and is highly tuned (shared buffers, work_mem, etc.). |
| **`beagle_pgbouncer`** | Connection pooler for Postgres. Configures `pgbouncer.ini` on‑the‑fly and forwards health checks to the Postgres instance. |
| **`beagle_memcached`** | 1.6.37 memcached for caching, health‑checked via `nc`. |
| **`beagle_rabbitmq`** | RabbitMQ 4.0.6‑management‑alpine with two users (`ECHO_RABBITMQ_USERNAME`, `DATADOG_RABBITMQ_USERNAME`). Exposes management UI on `${BEAGLE_RABBITMQ_MANAGEMENT_PORT}`. |
| **`beagle`** | Main Beagle web service (Gunicorn). Runs migrations, creates superuser if needed, collects static files and serves the Django app. |
| **`beagle_celery_beat`** | Celery beat scheduler for periodic tasks. |
| **`beagle_celery_default_queue`** | Default Celery worker queue (`${BEAGLE_DEFAULT_QUEUE}`). |
| **`beagle_celery_check_files_queue`** | Dedicated worker for the `check_files` queue. |
| **`beagle_celery_job_scheduler_queue`** | Dedicated worker for the `job_scheduler` queue. |
| **`beagle_echo_consumer`** | Runs the Echo consumer (`run_echo_consumer`). |
| **`beagle_smile_consumer`** | Runs the SMILE consumer (`run_smile_consumer`). |
| **`beagle_celery_runner_queue`** | Worker for the `runner` queue. |
| **`beagle_logrotate`** | Log rotation utility (creates config, runs `supercronic`). |
| **`beagle_db_backup`** | Daily database backup via `db_backup.cron`. |
| **`beagle_db_monthly_backup`** | Monthly backup via `db_monthly_backup.cron`. |

---

## 3. Networking

All services join the external network:

```yaml
networks:
  voyager_net:
    name: voyager_network_${BEAGLE_DEPLOYMENT}
    external: true
```

Make sure the network exists before bringing up the stack:

```bash
docker network create voyager_network_${BEAGLE_DEPLOYMENT}
```

---

## 4. Key Environment Variables

| Variable | Default / Example | Purpose |
|----------|-------------------|---------|
| `BEAGLE_DEPLOYMENT` | `dev` | Deployment environment (affects container names). |
| `BEAGLE_VERSION` | `latest` | Docker image tag for Beagle. |
| `DOCKER_UID`, `DOCKER_GID` | Current user IDs | Ensures file permissions match host. |
| `BEAGLE_DB_USERNAME`, `BEAGLE_DB_PASSWORD`, `BEAGLE_DB_NAME` | `beagle_user`, etc. | Credentials for Postgres. |
| `BEAGLE_RABBITMQ_USERNAME`, `DATADOG_RABBITMQ_USERNAME` | `guest`, etc. | RabbitMQ users. |
| `BEAGLE_PORT`, `BEAGLE_HOST` | `8000`, `localhost` | Web server binding. |
| `BEAGLE_DEFAULT_QUEUE`, `BEAGLE_CHECK_FILES_QUEUE`, `BEAGLE_JOB_SCHEDULER_QUEUE`, `BEAGLE_RUNNER_QUEUE` | `default`, etc. | Celery queue names. |
| `CLUSTER_FILESYSTEM_MOUNT`, `CLUSTER_SCRATCH_MOUNT` | Paths on the host | Mount points for shared storage. |
| `LOGROTATE_*`, `DB_BACKUP_*` | Cron expressions & limits | Rotation and backup schedules. |

---

## 5. Running the Stack

```bash
# 1. Create external network if not present
docker network create voyager_network_${BEAGLE_DEPLOYMENT}

# 2. Build the Beagle image (if not already available)
docker compose build

# 3. Start all services
docker compose up -d
```

### Health Checks

Each service has a `healthcheck` that Docker will use to determine readiness. If any dependent service is unhealthy, Docker Compose will wait until it becomes healthy before starting dependent containers.

---

## 6. Common Operations

| Operation | Command |
|-----------|---------|
| **Stop all services** | `docker compose down` |
| **View logs for a service** | `docker compose logs <service>` |
| **Enter a running container** | `docker compose exec <service> /bin/bash` |
| **Run migrations manually** | `docker compose run --rm beagle python manage.py migrate` |
| **Create a superuser** | `docker compose run --rm beagle python manage.py createsuperuser` |

---

## 7. Customizing the Stack

* **Add a new Celery queue** – Duplicate an existing worker service, change `command` and `healthcheck`, and add a new environment variable for the queue name.
* **Change database tuning** – Modify `command` arguments under `beagle_postgres`.
* **Adjust backup frequency** – Edit `DB_BACKUP_CRON` or `DB_MONTHLY_BACKUP_CRON` in `.env`. |

---

## 8. Security Notes

* **User permissions** – All services run under `${DOCKER_UID}:${DOCKER_GID}` to match host ownership.
* **Secrets** – Do not commit the `.env` file. Use environment variables or Docker secrets in production.
* **Port exposure** – Only expose necessary ports (`BEAGLE_PORT`, RabbitMQ management). Keep them behind a firewall or VPN in production.

---

## 9. Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| **Database connection failures** | Wrong `BEAGLE_DB_URL` or credentials | Verify `.env`, check Postgres logs. |
| **Celery workers not starting** | Healthcheck failure or missing queue name | Ensure `BEAGLE_DEFAULT_QUEUE` etc. are set, check logs. |
| **Logs not rotating** | `beagle_logrotate` not healthy | Verify cron schedule, log paths, and that `supercronic` is running. |
| **Backup not created** | Cron mis‑config or missing `PGPASSWORD` | Check `DB_BACKUP_CRON`, ensure `BEAGLE_DB_PASSWORD` is set. |

---

### Summary

This Compose file orchestrates a full Beagle deployment: web server, database, caching, messaging, workers, logging, and backups. Adjust environment variables in `.env`, ensure the external network exists, and run `docker compose up -d` to launch everything. Happy running!
