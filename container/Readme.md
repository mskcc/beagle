## Beagle Server

#### Build SIF

By default the container uses the `master` branch of beagle. To specify a custom github branch, set it in the `SINGULARITYENV_BEAGLE_BRANCH` environment variable.

```
export SINGULARITYENV_BEAGLE_BRANCH=master # branch on github to use on build; can set to any existing branch in repo
sudo -E singularity build beagle_service.sif beagle_service.def
```

Building SIF inside the docker image

If you do not have a singularity installed locally but you have docker you can use docker image to build singularity SIF.

`docker run --privileged -it -v /path/to/beagle:/beagle:rw  --entrypoint "/bin/bash" singularityware/singularity:v3.3.0`


Building Pooling Service

```
export SINGULARITYENV_DB_NAME=<db_name>
export SINGULARITYENV_DB_HOST=<db_host>
export SINGULARITYENV_DB_USER=<db_user>
export SINGULARITYENV_DB_PASSWORD=<db_password>
export SINGULARITYENV_DB_PORT=<db_port>
export SINGULARITYENV_LISTEN_PORT=<db_listen_port>
export SINGULARITYENV_MAX_DB_CONNECTIONS=<db_max_connections>
export SINGULARITYENV_DEFAULT_POOL_SIZE=<db_default_pool_size>
export SINGULARITYENV_MAX_CLIENT_CONN=<db_max_client_connections>
```

`singularity build pooling_service.sif pooling_service.def`

#### Expected Instance Run Variables

The following prepended singularity environment variables must be set so that the instance can run properly.

Note: Singularity passes environment variables to the SIF container by prepending variable names with `SINGULARITYENV_`. For example, to set `BEAGLE_PORT` in the container, you must set `SINGULARITYENV_BEAGLE_PORT`.
```
SINGULARITYENV_BEAGLE_DB_NAME
SINGULARITYENV_BEAGLE_DB_USERNAME
SINGULARITYENV_BEAGLE_DB_PASSWORD
SINGULARITYENV_BEAGLE_DB_PORT
SINGULARITYENV_FLOWER_PORT
SINGULARITYENV_BEAGLE_PORT
SINGULARITYENV_BEAGLE_LOG_PATH
SINGULARITYENV_BEAGLE_PATH
SINGULARITYENV_BEAGLE_URL
SINGULARITYENV_BEAGLE_ALLOWED_HOSTS
SINGULARITYENV_BEAGLE_POOLED_NORMAL_FILE_GROUP
SINGULARITYENV_BEAGLE_DMP_BAM_FILE_GROUP
SINGULARITYENV_BEAGLE_NOTIFIERS
SINGULARITYENV_GIT_SSH_COMMAND
SINGULARITYENV_BEAGLE_AUTH_LDAP_SERVER_URI
SINGULARITYENV_BEAGLE_RIDGEBACK_URL
SINGULARITYENV_BEAGLE_RABIX_URL
SINGULARITYENV_BEAGLE_RABIX_PATH
SINGULARITYENV_BEAGLE_RABBITMQ_USERNAME
SINGULARITYENV_BEAGLE_RABBITMQ_PASSWORD
SINGULARITYENV_CELERY_BROKER_URL
SINGULARITYENV_BEAGLE_LIMS_USERNAME
SINGULARITYENV_BEAGLE_LIMS_PASSWORD
SINGULARITYENV_BEAGLE_RUNNER_QUEUE
SINGULARITYENV_BEAGLE_DEFAULT_QUEUE
SINGULARITYENV_BEAGLE_JOB_SCHEDULER_QUEUE
SINGULARITYENV_JIRA_USERNAME
SINGULARITYENV_JIRA_PASSWORD
SINGULARITYENV_JIRA_URL
SINGULARITYENV_JIRA_PROJECT
```

The following are optional environmental variables for use with `beagle` and `celery`. It is recommended to set `SINGULARITYENV_CELERY_LOG_PATH` for debugging/logging purposes.

```
SINGULARITYENV_BEAGLE_PATH # beagle install to use if not using what's in container; default is /usr/bin/beagle
SINGULARITYENV_CELERY_LOG_PATH # location of where to store log files for celery; default is /tmp
SINGULARITYENV_CELERY_PID_PATH # where to store pid files for celery workers; default is /tmp
SINGULARITYENV_BEAT_SCHEDULE_PATH # where to store schedule of celery beat; default is /tmp
SINGULARITYENV_EVENT QUEUE PREFIX # prefix for event queue; default is runtime timestamp
```

For more detailed information about beagles environment, you can use the beagle [environment page](../docs/ENVIRONMENT_VARIABLES.md)

#### Running an instance

Running the following command will create a beagle instance named `beagle_service`
```
singularity instance start beagle_service.sif beagle_service
```

This is accessible through the port number set through `SINGULARITYENV_BEAGLE_PORT`

For example, if `SINGULARITYENV_BEAGLE_PORT=4001` on a machine called `silo`:

```
http://silo:4001
```
