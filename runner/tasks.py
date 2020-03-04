import os
import uuid
import logging
import requests
from celery import shared_task
from django.conf import settings
from runner.run.objects.run_object import RunObject
from .models import Run, RunStatus, Port, PortType, OperatorRun, TriggerAggregateConditionType, TriggerRunType, OperatorTrigger
from runner.operator import OperatorFactory
from beagle_etl.models import Operator
from runner.exceptions import RunCreateException


logger = logging.getLogger(__name__)


def create_jobs_from_operator(operator):
    jobs = operator.get_jobs()

    valid_jobs, invalid_jobs = [], []
    for job in jobs:
        valid_jobs.append(job) if job[0].is_valid() else invalid_jobs.append(job)

    operator_run = OperatorRun.objects.create(operator=operator.model, num_total_runs=len(valid_jobs))

    for job in valid_jobs:
        logger.info("Creating Run object")
        run = job[0].save(operator_run_id=operator_run.id)
        logger.info("Run object created with id: %s" % str(run.id))
        create_run_task.delay(str(run.id), job[1], None)

    for job in invalid_jobs:
        logger.error("Job invalid: %s" % str(job[0].errors))

    operator_run.status = RunStatus.RUNNING
    operator_run.save()


@shared_task
def create_jobs_from_request(request_id, operator_id):
    logger.info("Creating operator id %s for requestId: %s" % (operator_id, request_id))
    operator_model = Operator.objects.get(id=operator_id)
    operator = OperatorFactory.get_by_model(operator_model, request_id=request_id)
    create_jobs_from_operator(operator)


@shared_task
def create_jobs_from_chaining(to_operator_id, from_operator_id, run_ids=[]):
    logger.info("Creating operator id %s from chaining: %s" % (to_operator_id, from_operator_id))
    operator_model = Operator.objects.get(id=to_operator_id)
    operator = OperatorFactory.get_by_model(operator_model, run_ids=run_ids)
    create_jobs_from_operator(operator)


@shared_task
def process_triggers():
    operator_runs = OperatorRun.objects.prefetch_related(
        'trigger', 'runs', 'operator__from_triggers'
    ).exclude(status__in=[RunStatus.COMPLETED, RunStatus.FAILED])

    for operator_run in operator_runs:
        try:
            for trigger in operator_run.operator.from_triggers.all():
                trigger_type = trigger.run_type

                if trigger_type == TriggerRunType.AGGREGATE:
                    condition = trigger.aggregate_condition
                    if condition == TriggerAggregateConditionType.ALL_RUNS_SUCCEEDED:
                        if operator_run.percent_runs_succeeded == 100.0:
                            operator_run.complete()
                            create_jobs_from_chaining.delay(
                                trigger.to_operator_id,
                                trigger.from_operator_id,
                                list(operator_run.runs.values_list('id', flat=True))
                            )
                            continue
                    elif condition == TriggerAggregateConditionType.NINTY_PERCENT_SUCCEEDED:
                        if operator_run.percent_runs_succeeded >= 90.0:
                            operator_run.complete()
                            create_jobs_from_chaining.delay(
                                trigger.to_operator_id,
                                trigger.from_operator_id,
                                list(operator_run.runs.values_list('id', flat=True))
                            )
                            continue

                    if operator_run.percent_runs_finished == 100.0:
                        logger.info("Condition never met for operator run %s" % operator_run.id)
                        operator_run.fail()

                elif trigger_type == TriggerRunType.INDIVIDUAL:
                    if operator_run.percent_runs_finished == 100.0:
                        operator_run.complete()

            if operator_run.percent_runs_finished == 100.0:
                if operator_run.percent_runs_succeeded == 100.0:
                    operator_run.complete()
                else:
                    operator_run.fail()

        except Exception as e:
            logger.info("Trigger %s Fail. Error %s" % (operator_run.id, str(e)))
            operator_run.fail()


@shared_task
def create_run_task(run_id, inputs, output_directory=None):
    logger.info("Creating and validating Run")
    try:
        run = RunObject.from_cwl_definition(run_id, inputs)
        run.ready()
    except RunCreateException as e:
        run = RunObject.from_db(run_id)
        run.fail(e)
        RunObject.to_db(run)
        logger.info("Run %s Failed" % run_id)
    else:
        RunObject.to_db(run)
        submit_job.delay(run_id, output_directory)
        logger.info("Run %s Ready" % run_id)


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


def fail_job(run_id, error_message):
    run = RunObject.from_db(run_id)
    run.fail(error_message)
    run.to_db()


def complete_job(run_id, outputs):
    run = RunObject.from_db(run_id)
    run.complete(outputs)
    run.to_db()

    for trigger in run.run_obj.operator_run.operator.from_triggers.filter(run_type=TriggerRunType.INDIVIDUAL):
        create_jobs_from_chaining.delay(
            trigger.to_operator_id,
            trigger.from_operator_id,
            [run_id]
        )


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
                    # TODO: Fetch error message from Executor here
                    fail_job(str(run.id),
                             'Job failed. You can find logs in /work/pi/beagle/work/%s' %
                             str(run.execution_id))
                    continue
                if remote_status['status'] == 'COMPLETED':
                    logger.info("Job %s [%s] COMPLETED" % (run.id, run.execution_id))
                    complete_job(str(run.id), remote_status['outputs'])
                    continue
                if remote_status['status'] == 'CREATED' or remote_status['status'] == 'PENDING' or remote_status['status'] == 'RUNNING':
                    logger.info("Job %s [%s] RUNNING" % (run.id, run.execution_id))
                    running_job(run)
                    continue
            else:
                logger.error("Failed to check status for job: %s [%s]" % (run.id, run.execution_id))
        else:
            logger.error("Job %s not submitted" % str(run.id))
