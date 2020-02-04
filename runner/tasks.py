import uuid
import os
import logging
import requests
import runner.run.run_creator
import importlib
from celery import shared_task
from django.conf import settings
from .models import Run, RunStatus, Port, PortType
from runner.operator import OperatorFactory
from runner.pipeline.pipeline_resolver import CWLResolver
from beagle_etl.models import Operator


logger = logging.getLogger(__name__)



@shared_task
def create_jobs_from_request(request_id, operator_id):
    logger.info("Creating operator id %s for requestId: %s" % (operator_id, request_id))
    operator_info = Operator.objects.get(id=operator_id)
    operator = OperatorFactory.get_by_class_name(operator_info.class_name, request_id)

    jobs = operator.get_jobs()

    for job in jobs:
        if job[0].is_valid():
            logger.info("Creating Run object")
            run = job[0].save()
            logger.info("Run object created with id: %s" % str(run.id))
            create_run_task.delay(str(run.id), job[1], None)
        else:
            logger.error("Job invalid: %s" % str(job[0].errors))


# TODO remove this when the Celery backlog is flushed and OperatorViewSet is updated
@shared_task
def operator_job(request_id, pipeline_type):
    warnings.warn("operator_job to be deprecated for create_jobs_from_request", DeprecationWarning, stacklevel=2)
    logger.info("Creating operator %s for requestId: %s" % (pipeline_type, request_id))
    operator = OperatorFactory.factory(pipeline_type, request_id)
    jobs = operator.get_jobs()
    for job in jobs:
        if job[0].is_valid():
            logger.info("Creating Run object")
            run = job[0].save()
            logger.info("Run object created with id: %s" % str(run.id))
            create_run_task.delay(str(run.id), job[1], None)
        else:
            logger.error("Job invalid: %s" % str(job[0].errors))


@shared_task
def create_run_task(run_id, inputs, output_directory=None):
    logger.info("Creating and validating Run")
    try:
        run = Run.objects.get(id=run_id)
    except Run.DoesNotExist:
        raise Exception("Failed to create a run")
    cwl_resolver = CWLResolver(run.app.github, run.app.entrypoint, run.app.version)
    resolved_dict = cwl_resolver.resolve()
    try:
        task = runner.run.run_creator.Run(run_id, resolved_dict, inputs)
        for input in task.inputs:
            port = Port(run=run, name=input.id, port_type=input.type, schema=input.schema,
                        secondary_files=input.secondary_files, db_value=input.db_value, value=input.value)
            port.save()
        for output in task.outputs:
            port = Port(run=run, name=output.id, port_type=output.type, schema=output.schema,
                        secondary_files=output.secondary_files, db_value=output.value)
            port.save()
    except Exception as e:
        run.status = RunStatus.FAILED
        run.job_statuses = {'error': 'Error during creation because of %s' % str(e)}
        run.save()
    else:
        run.status = RunStatus.READY
        run.save()
        submit_job.delay(run_id, output_directory)
        logger.info("Run created")


@shared_task
def submit_job(run_id, output_directory=None):
    try:
        run = Run.objects.get(id=run_id)
    except Run.DoesNotExist:
        raise Exception("Failed to submit a run")
    app = {
        "github": {
            "repository": run.app.github,
            "entrypoint": run.app.entrypoint,
            "version": run.app.version
        }
    }
    inputs = dict()
    for port in run.port_set.filter(port_type=PortType.INPUT).all():
        inputs[port.name] = port.value
    if not output_directory:
        output_directory = os.path.join(run.app.output_directory, str(run_id))
    job = {
        'app': app,
        'inputs': inputs,
        'root_dir': output_directory
    }
    logger.info("Job %s ready for submitting" % run_id)
    response = requests.post(settings.RIDGEBACK_URL + '/v0/jobs/', json=job)
    if response.status_code == 201:
        run.execution_id = response.json()['id']
        run.status = RunStatus.RUNNING
        logger.info("Job %s successfully submitted with id:%s" % (run_id, run.execution_id))
        run.save()
    else:
        logger.info("Failed to submit job %s" % run_id)
        run.status = RunStatus.FAILED
        run.save()


def check_status_on_ridgeback(job_id):
    response = requests.get(settings.RIDGEBACK_URL + '/v0/jobs/%s/' % job_id)
    if response.status_code == 200:
        logger.info("Job %s in status: %s" % (job_id, response.json()['status']))
        return response.json()
    logger.error("Failed to fetch job status for: %s" % job_id)
    return None


def fail_job(run):
    run.status = RunStatus.FAILED
    run.save()


def complete_job(run, remote_status):
    run.status = RunStatus.COMPLETED
    file_group = run.app.output_file_group
    for k, v in remote_status['outputs'].items():
        port = run.port_set.filter(port_type=PortType.OUTPUT, name=k).first()
        port.value = v
        port.db_value = runner.run.run_creator._resolve_outputs(v, file_group, run.output_metadata)
        port.save()
    run.save()


def running_job(run):
    run.status = RunStatus.RUNNING
    run.save()


@shared_task
def check_jobs_status():
    runs = Run.objects.filter(status__in=(RunStatus.RUNNING, RunStatus.READY)).all()
    for run in runs:
        if run.execution_id:
            logger.info("Checking status for job: %s [%s]" % (run.id, run.execution_id))
            remote_status = check_status_on_ridgeback(run.execution_id)
            if remote_status:
                if remote_status['status'] == 'FAILED':
                    logger.info("Job %s [%s] FAILED" % (run.id, run.execution_id))
                    fail_job(run)
                    continue
                if remote_status['status'] == 'COMPLETED':
                    logger.info("Job %s [%s] COMPLETED" % (run.id, run.execution_id))
                    complete_job(run, remote_status)
                    continue
                if remote_status['status'] == 'CREATED' or remote_status['status'] == 'PENDING' or remote_status['status'] == 'RUNNING':
                    logger.info("Job %s [%s] RUNNING" % (run.id, run.execution_id))
                    running_job(run)
                    continue
            else:
                logger.error("Failed to check status for job: %s [%s]" % (run.id, run.execution_id))
        else:
            logger.error("Job %s not submitted" % str(run.id))
