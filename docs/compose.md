# Beagle Compose File – `compose.yaml`

The Docker compose file defines the entire runtime environment for **Beagle**, including the database, rabbitmq, and celery workers.

> **Tip** – All environment variables are sourced from the `.env` file in the project root.

## 1. Services

| Service                                 | Description                                                                                                                   |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **`beagle_create_volumes`**             | Creates all data volumes                                                                                                      |
| **`beagle_postgres`**                   | PostgreSQL 17 instance. Configured to be highly tuned (shared buffers, work_mem, etc.).                                       |
| **`beagle_pgbouncer`**                  | Connection pooling for Postgres.                                                                                              |
| **`beagle_memcached`**                  | Memcached service for caching.                                                                                                |
| **`beagle_rabbitmq`**                   | RabbitMQ 4 with users for multi-service integration. Has an accessible management UI on `${BEAGLE_RABBITMQ_MANAGEMENT_PORT}`. |
| **`beagle`**                            | Main Beagle web service. Runs migrations, creates superuser if needed, collects static files and serves the Django app.       |
| **`beagle_celery_beat`**                | Celery beat scheduler for periodic tasks.                                                                                     |
| **`beagle_celery_default_queue`**       | Default Celery worker queue (`${BEAGLE_DEFAULT_QUEUE}`).                                                                      |
| **`beagle_celery_check_files_queue`**   | Dedicated worker for the `check_files` queue.                                                                                 |
| **`beagle_celery_job_scheduler_queue`** | Dedicated worker for the `job_scheduler` queue.                                                                               |
| **`beagle_echo_consumer`**              | Runs the Echo consumer (`run_echo_consumer`).                                                                                 |
| **`beagle_smile_consumer`**             | Runs the SMILE consumer (`run_smile_consumer`).                                                                               |
| **`beagle_celery_runner_queue`**        | Worker for the `runner` queue.                                                                                                |
| **`beagle_logrotate`**                  | Log rotation utility                                                                                                          |
| **`beagle_db_backup`**                  | Daily database backup via `db_backup.cron`.                                                                                   |
| **`beagle_db_monthly_backup`**          | Monthly backup via `db_monthly_backup.cron`.                                                                                  |

## 2. Networking

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

## If you are deploying [Ridgeback](https://github.com/mskcc/ridgeback) as well, the network should already by created.

## 3. Key Environment Variables

| Variable                                                                                                | Default / Example                            | Purpose                                           |
| ------------------------------------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------- |
| `BEAGLE_DEPLOYMENT`                                                                                     | `dev`                                        | Deployment environment (affects container names). |
| `BEAGLE_VERSION`                                                                                        | `latest`                                     | Docker image tag for Beagle.                      |
| `DOCKER_UID`, `DOCKER_GID`                                                                              | `000000000`                                  | Ensures file permissions match host.              |
| `BEAGLE_DB_USERNAME`, `BEAGLE_DB_PASSWORD`, `BEAGLE_DB_NAME`                                            | `beagle_user`                                | Credentials for Postgres.                         |
| `BEAGLE_RABBITMQ_USERNAME`, `DATADOG_RABBITMQ_USERNAME`                                                 | `guest`                                      | RabbitMQ users.                                   |
| `BEAGLE_PORT`, `BEAGLE_HOST`                                                                            | `8000`, `localhost`                          | Web server binding.                               |
| `BEAGLE_DEFAULT_QUEUE`, `BEAGLE_CHECK_FILES_QUEUE`, `BEAGLE_JOB_SCHEDULER_QUEUE`, `BEAGLE_RUNNER_QUEUE` | `default`                                    | Celery queue names.                               |
| `CLUSTER_FILESYSTEM_MOUNT`, `CLUSTER_SCRATCH_MOUNT`                                                     | `/data1/core006`                             | Mount points for shared storage.                  |
| `CLUSTER_CODE_PATH`                                                                                     | `/data1/core006/beagle`                      | Path for the beagle code base on the cluster      |
| `LOGROTATE_*`, `DB_BACKUP_*`                                                                            | `*_NUM_ROTATIONS=20` `*_CRON="0 1,20 * * *"` | Log rotation and backup schedules.                |

## 4. Running the Stack

```bash
# 1. Create external network if not present
docker network create voyager_network_${BEAGLE_DEPLOYMENT}

# 2. Start all services in the background
docker compose up -d
```

### Health Checks

Each service has a `healthcheck` that Docker will use to determine readiness. If any dependent service is unhealthy, Docker Compose will wait until it becomes healthy before starting dependent containers. Any service that turns unhealthy will be automatically restarted.

## 5. Common Operations

| Operation                     | Command                                                                              |
| ----------------------------- | ------------------------------------------------------------------------------------ |
| **Stop all services**         | `docker compose down`                                                                |
| **View logs for a service**   | `docker compose logs <service>`                                                      |
| **Enter a running container** | `docker compose exec <service> /bin/bash`                                            |
| **Run migrations manually**   | `docker compose run --rm beagle python $CLUSTER_CODE_PATH/manage.py migrate`         |
| **Create a superuser**        | `docker compose run --rm beagle python $CLUSTER_CODE_PATH/manage.py createsuperuser` |

## 6. Customizing the Stack

- **Add a new Celery queue** – Duplicate an existing worker service, change `command` and `healthcheck`, and add a new environment variable for the queue name.
- **Change database tuning** – Modify `command` arguments under `beagle_postgres`.
- **Adjust backup frequency** – Edit `DB_BACKUP_CRON` or `DB_MONTHLY_BACKUP_CRON` in `.env`. |

## 7. Security Notes

- **User permissions** – All services run under the service user with `${DOCKER_UID}:${DOCKER_GID}` to match host ownership.
- **Secrets** – Do not commit the `.env` file. The file is version controlled on the internal mskcc github repo
- **Port exposure** – Only expose necessary ports (`BEAGLE_PORT`, RabbitMQ management).

## 8. Troubleshooting

| Symptom                          | Likely Cause                                | Fix                                                                 |
| -------------------------------- | ------------------------------------------- | ------------------------------------------------------------------- |
| **Database connection failures** | Wrong `BEAGLE_DB_URL` or credentials        | Verify `.env`, check Postgres logs.                                 |
| **Celery workers not starting**  | Healthcheck failure or missing queue name   | Ensure `BEAGLE_DEFAULT_QUEUE` etc. are set, check logs.             |
| **Logs not rotating**            | `beagle_logrotate` not healthy              | Verify cron schedule, log paths, and that `supercronic` is running. |
| **Backup not created**           | Cron missconfigured or missing `PGPASSWORD` | Check `DB_BACKUP_CRON`, ensure `BEAGLE_DB_PASSWORD` is set.         |
