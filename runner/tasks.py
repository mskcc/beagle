import logging
import json
from .models import Run, RunStatus, Port, PortType
from celery import shared_task
import requests
import runner.run.run_creator
from runner.operator.operator import OperatorFactory
from runner.pipeline.pipeline_resolver import CWLResolver


logger = logging.getLogger(__name__)


@shared_task
def operator_job(request_id, pipeline_type):
    logger.info("Creating operator %s for requestId: %s" % (pipeline_type, request_id))
    operator = OperatorFactory.factory(pipeline_type, request_id)
    jobs = operator.get_jobs()
    for job in jobs:
        if job[0].is_valid():
            run = job[0].save()
            logger.debug(run.id)
            create_run_task.delay(str(run.id), job[1])
        else:
            logger.debug(job[0].errors)


@shared_task
def create_run_task(run_id, inputs):
    logger.info("Creating and validating Run")
    try:
        run = Run.objects.get(id=run_id)
    except Run.DoesNotExist:
        raise Exception("Failed to create a run")
    cwl_resolver = CWLResolver(run.app.github, run.app.entrypoint, run.app.version)
    resolved_dict = cwl_resolver.resolve()
    task = runner.run.run_creator.Run(resolved_dict, inputs)
    for input in task.inputs:
        port = Port(run=run, name=input.id, port_type=input.type, schema=input.schema,
                    secondary_files=input.secondary_files, db_value=inputs[input.id], value=input.value)
        port.save()
    for output in task.outputs:
        port = Port(run=run, name=output.id, port_type=output.type, schema=output.schema,
                    secondary_files=output.secondary_files, db_value=output.value)
        port.save()
    run.status = RunStatus.READY
    submit_job.delay(run_id)
    logger.info("Run created")


@shared_task
def submit_job(run_id):
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
    job = {
        'app' : app,
        'inputs': inputs
    }
    logger.info("Ready for submittion")
    response = requests.post('http://silo:5003/v0/jobs/', json=json.dumps(job))
    if response.status_code == 201:
        logger.info("Successfully for submitted")
        run.execution_id = response.json()['id']
        run.status = RunStatus.RUNNING
        run.save()
    else:
        logger.info("Failed to submit")
        run.status = RunStatus.FAILED
        run.save()


def check_status_on_ridgeback(job_id):
    response = requests.get('http://silo:5003/v0/jobs/%s/' % job_id)
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
        port = run.port_set.filter(port_type=PortType.OUTPUT, name=k)
        port.value = v
        port.db_value = runner.run.run_creator._resolve_outputs(v, file_group)
        port.save()
    run.save()


def running_job(run):
    run.status = RunStatus.RUNNING
    run.save()


@shared_task
def check_jobs_status():
    runs = Run.objects.filter(status__in=(RunStatus.RUNNING, RunStatus.READY)).all()
    for run in runs:
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
        logger.error("Failed to check status for job: %s [%s]" % (run.id, run.execution_id))




