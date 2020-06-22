#!/bin/bash

if [ ! "$1" ] || [ ! "$2" ] || [ ! "$3" ]; then
    echo "run_beagle.sh <environment> <config> <version>"
    exit 1
fi

if [ $1 != "production" ] && [ $1 != "staging" ]; then
    echo "Environment needs to be production or staging"
    exit 1
fi

if [ ! -f $2 ]; then
    echo "Config needs to be a path: $2"
    exit 1
fi

module load singularity/3.3.0
echo "Loading configuration from $2"
source $2

echo "Stopping $1 environment"
singularity instance stop $1_beagle_services
singularity instance stop $1_beagle_celery

echo Starting $1 environment version $3

if [ $1 != "production" ]; then
    singularity instance start --containall --bind /srv/services/voyager/ --bind /home/ivkovic/rabix-cli-1.0.5 --bind /tmp --bind /ifs --bind /juno/work/ci /srv/services/voyager/beagle_service_%3.sif $1_beagle_services
    singularity instance start --containall --bind /srv/services/voyager/ --bind /home/ivkovic/rabix-cli-1.0.5 --bind /tmp --bind /ifs --bind /juno/work/ci /srv/services/voyager/beagle_celery_%3.sif $1_beagle_celery
else
    singularity instance start --containall --bind /srv/services/staging_voyager/ --bind /home/ivkovic/rabix-cli-1.0.5 --bind /tmp --bind /ifs --bind /juno/work/ci /srv/services/staging_voyager/beagle_service_$3.sif $1_beagle_services
    singularity instance start --containall --bind /srv/services/staging_voyager/ --bind /home/ivkovic/rabix-cli-1.0.5 --bind /tmp --bind /ifs --bind /juno/work/ci /srv/services/staging_voyager/beagle_celery_$3.sif $1_beagle_celery
fi