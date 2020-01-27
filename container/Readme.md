## Beagle Server

#### Build SIF

By default the container uses the `master` branch of beagle. To specify a custom github branch, set it in the `SINGULARITYENV_BEAGLE_BRANCH` environment variable.

```
export SINGULARITYENV_BEAGLE_BRANCH=master # branch on github to use on build; can set to any existing branch in repo
sudo -E singularity build beagle_service.sif beagle_service.def
```

#### Expected Instance Run Variables

The following prepended singularity environment variables must be set so that the instance can run properly.

Note: Singularity passes environment variables to the SIF container by prepending variable names with `SINGULARITYENV_`. For example, to set `BEAGLE_PORT` in the container, you must set `SINGULARITYENV_BEAGLE_PORT`.
```
SINGULARITYENV_BEAGLE_PORT
SINGULARITYENV_BEAGLE_RIDGEBACK_URL
SINGULARITYENV_BEAGLE_DB_NAME
SINGULARITYENV_BEAGLE_DB_USERNAME
SINGULARITYENV_BEAGLE_DB_PASSWORD
SINGULARITYENV_BEAGLE_DB_PORT
SINGULARITYENV_BEAGLE_AUTH_LDAP_SERVER_URI
SINGULARITYENV_BEAGLE_RABIX_URL
SINGULARITYENV_BEAGLE_RABBITMQ_USERNAME
SINGULARITYENV_BEAGLE_RABBITMQ_PASSWORD
SINGULARITYENV_BEAGLE_LIMS_USERNAME
SINGULARITYENV_BEAGLE_LIMS_PASSWORD
SINGULARITYENV_BEAGLE_LIMS_URL
SINGULARITYENV_BEAGLE_RABIX_PATH
SINGULARITYENV_BEAGLE_RUNNER_QUEUE
SINGULARITYENV_BEAGLE_DEFAULT_QUEUE
SINGULARITYENV_BEAGLE_JOB_SCHEDULER_QUEUE
SINGULARITYENV_CELERY_EVENT_QUEUE_PREFIX
```

The following are optional environmental variables for use with `beagle` and `celery`. It is recommended to set `SINGULARITYENV_CELERY_LOG_PATH` for debugging/logging purposes.

```
SINGULARITYENV_BEAGLE_PATH # beagle install to use if not using what's in container; default is /usr/bin/beagle
SINGULARITYENV_CELERY_LOG_PATH # location of where to store log files for celery; default is /tmp
SINGULARITYENV_CELERY_PID_PATH # where to store pid files for celery workers; default is /tmp
SINGULARITYENV_BEAT_SCHEDULE_PATH # where to store schedule of celery beat; default is /tmp
SINGULARITYENV_EVENT QUEUE PREFIX # prefix for event queue; default is runtime timestamp
```

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
