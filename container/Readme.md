## Beagle Server

#### Build SIF

```
sudo singularity build beagle_service.sif beagle_service.def
```

#### Expected Variables

The following environment variables must be set so that the instance can run properly.

Note: Singularity passes environment variables to the SIF container by prepending variable names with `SINGULARITYENV_`. For example, to set `BEAGLE_PORT` in the container, you must set `SINGULARITYENV_BEAGLE_PORT`.

```
SINGULARITYENV_BEAGLE_PORT
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
