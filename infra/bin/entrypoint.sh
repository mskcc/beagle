#!/bin/bash
set -e

# Wait for Postgres
# We use the env vars from .env.${ENV}, where ENV=staging|prod
echo "Waiting for postgres..."
while ! nc -z $BEAGLE_DB_URL $BEAGLE_DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

if [ "$(id -u)" = '0' ]; then
  echo "Configuring system users for MSKCC Cluster..."
  sed -i 's/UID_MAX.*/UID_MAX 6000000000/g' /etc/login.defs
  sed -i 's/GID_MAX.*/GID_MAX 6000000000/g' /etc/login.defs

  # Add groups from .env.${ENV}
  for single_group in ${all_groups}; do
    # logic to add groups based on all_groups variable
  done

  # Create the app user if it doesn't exist
  id -u ${DOCKER_USERNAME} &>/dev/null || useradd -s /bin/bash --uid ${DOCKER_UID} -m ${DOCKER_USERNAME}
fi

# Database Maintenance
echo "Applying database migrations..."
python3 manage.py migrate --noinput

# Static Files
echo "Collecting static files..."
python3 manage.py collectstatic --noinput

# Hand off to the command (Gunicorn)
echo "Starting Beagle..."
exec "$@"
