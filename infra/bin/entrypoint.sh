#!/bin/bash
set -e

# 1. Wait for Postgres
echo "Waiting for postgres at $BEAGLE_DB_URL:$BEAGLE_DB_PORT..."
# Note: nc (netcat) needs to be installed in your Dockerfile
while ! nc -z "$BEAGLE_DB_URL" "$BEAGLE_DB_PORT"; do
  sleep 0.5
done
echo "PostgreSQL started"

# 2. MSKCC Cluster Configuration
if [ "$(id -u)" = '0' ]; then
  echo "Configuring system for MSKCC Cluster..."

  # Boost system limits for massive Cluster IDs
  sed -i 's/UID_MAX.*/UID_MAX 6000000000/g' /etc/login.defs
  sed -i 's/GID_MAX.*/GID_MAX 6000000000/g' /etc/login.defs

  # 3. Add groups from all_groups
  # If all_groups="DOCKER_GROUP_1 DOCKER_GROUP_2"
  if [ -n "$all_groups" ]; then
    for var_name in $all_groups; do
      # This is the "Indirect Expansion" bit: ${!var_name}
      # If var_name="DOCKER_GROUP_1", then group_info becomes "20131 voyager_group"
      group_info="${!var_name}"

      if [ -n "$group_info" ]; then
        # Split "20131 voyager_group" into ID and NAME
        g_id=$(echo "$group_info" | awk '{print $1}')
        g_name=$(echo "$group_info" | awk '{print $2}')

        # Check if group exists, if not, create it
        if ! getent group "$g_id" >/dev/null 2>&1; then
          echo "Creating group: $g_name ($g_id)"
          groupadd -g "$g_id" "$g_name"
        else
          echo "Group ID $g_id already exists."
        fi
      fi
    done
  fi

  # 4. Create the app user
  if [ -n "$DOCKER_USERNAME" ]; then
    if ! id -u "$DOCKER_USERNAME" >/dev/null 2>&1; then
      echo "Creating user $DOCKER_USERNAME with UID $DOCKER_UID"
      useradd -s /bin/bash --uid "$DOCKER_UID" -m "$DOCKER_USERNAME"
      # Add user to all groups we just created
      for var_name in $all_groups; do
        g_name=$(echo "${!var_name}" | awk '{print $2}')
        usermod -a -G "$g_name" "$DOCKER_USERNAME"
      done
    fi
  fi
fi

# 5. Database & Static Files
# Only run these if we are starting the main server (to avoid worker collisions)
if [[ "$*" == *"manage.py runserver"* ]] || [[ "$*" == *"gunicorn"* ]]; then
  echo "Applying database migrations..."
  python3 manage.py migrate --noinput
  echo "Collecting static files..."
  python3 manage.py collectstatic --noinput
fi

# 6. Hand off to the command
echo "Starting Beagle: $@"
exec "$@"
