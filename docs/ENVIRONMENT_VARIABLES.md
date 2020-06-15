
### General

General Beagle environment variables

 Environment       | Description |  Example |
 | :------------- |:-------------| :-------------|
BEAGLE_DB_NAME | PostgreSQL database | example_database
BEAGLE_DB_USERNAME | PostgreSQL user | example_user
BEAGLE_DB_PASSWORD | password for PostgreSQL user | example_password
BEAGLE_DB_PORT | PostgreSQL port | 3333
BEAGLE_PORT | Beagle port ( only for container use) | 4444
BEAGLE_LOG_PATH | log file | /example/path/logs/beagle-server.log
BEAGLE_PATH | Path to Beagle repo ( only for container use) | /srv/services/staging_voyager/beagle/
BEAGLE_URL | Url for beagle | http://your_server:4444
BEAGLE_ALLOWED_HOSTS | Hosts allowed to run Beagle | localhost,your_server
BEAGLE_POOLED_NORMAL_FILE_GROUP| File group for pooled normals, must be a uuid | 62033c45-6c55-4d2d-bec2-9c917b4af133
BEAGLE_DMP_BAM_FILE_GROUP | File group for DMP BAMS normal, must be a uuid |f62f5fb8-2dbd-45b2-8050-6dac56a4cc17
BEAGLE_NOTIFIERS| List of notifiers | JIRA

### Other services

Beagle environment variables needed to interact with other services
 Environment       | Description |  Example |
 | :------------- |:-------------| :-------------|
GIT_SSH_COMMAND | Git ssh command needed to clone private repos| ssh -i /path/to/id_rsa -o UserKnownHostsFile=/path/to/known_hosts -F /dev/null"
BEAGLE_AUTH_LDAP_SERVER_URI | LDAP server URI | ldaps://example.org/
BEAGLE_RIDGEBACK_URL | [Ridgeback](https://github.com/mskcc/ridgeback) URL | http://localhost:2000
BEAGLE_RABIX_URL | Rabix URL | http://localhost:2001
BEAGLE_RABIX_PATH | Path to Rabix binary | /path/to/rabix
BEAGLE_RABBITMQ_USERNAME | Rabbitmq username | example_username
BEAGLE_RABBITMQ_PASSWORD | Rabbitmq password | example_password
BEAGLE_LIMS_USERNAME | LIMS username | example_username
BEAGLE_LIMS_PASSWORD | LIMS password | example_password
BEAGLE_RUNNER_QUEUE | Rabbitmq runner queue | example.runner.queue
BEAGLE_DEFAULT_QUEUE | Rabbitmq default queue | example.runner.queue
BEAGLE_JOB_SCHEDULER_QUEUE | Rabbitmq scheduler queue | example.runner.queue
CELERY_EVENT_QUEUE_PREFIX | Prefix for Celery event | beagle.celery
CELERY_LOG_PATH | Log path for Celery | /path/to/celey.log
JIRA_USERNAME | JIRA username | example_username
JIRA_PASSWORD | JIRA password | example_password
JIRA_URL | JIRA URL | http://jira.example.org:5000
JIRA_PROJECT | JIRA Board | EXAMPLE_BOARD
