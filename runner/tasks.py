import os
import logging
import requests
import datetime
from urllib.parse import urljoin
from celery import shared_task
from django.conf import settings
from django.db.models import Count
from runner.run.objects.run_object import RunObject
from .models import Run, RunStatus, PortType, OperatorRun, TriggerAggregateConditionType, TriggerRunType, Pipeline
from notifier.events import RunFinishedEvent, OperatorRequestEvent, OperatorRunEvent, SetCIReviewEvent, \
    SetPipelineCompletedEvent, AddPipelineToDescriptionEvent, SetPipelineFieldEvent, OperatorStartEvent, SetLabelEvent, SetRunTicketInImportEvent
from notifier.tasks import send_notification, notifier_start
from runner.operator import OperatorFactory
from beagle_etl.jobs import TYPES
from beagle_etl.models import Operator, Job
from runner.exceptions import RunCreateException
from notifier.models import JobGroup, JobGroupNotifier
from file_system.repository import FileRepository


logger = logging.getLogger(__name__)


def create_jobs_from_operator(operator, job_group_id=None, job_group_notifier_id=None, parent=None):
    jobs = operator.get_jobs()
    create_operator_run_from_jobs(operator, jobs, job_group_id, job_group_notifier_id, parent)


def create_operator_run_from_jobs(operator, jobs, job_group_id=None, job_group_notifier_id=None, parent=None):
    jg = None
    jgn = None
    try:
        jg = JobGroup.objects.get(id=job_group_id)
        logger.info("JobGroup id: %s", job_group_id)
    except JobGroup.DoesNotExist:
        logger.info("JobGroup not set")
    try:
        jgn = JobGroupNotifier.objects.get(id=job_group_notifier_id)
    except JobGroupNotifier.DoesNotExist:
        logger.info("JobGroupNotifier not set")
    valid_jobs, invalid_jobs = [], []
    for job in jobs:
        valid_jobs.append(job) if job[0].is_valid() else invalid_jobs.append(job)

    try:
        operator_run_parent = OperatorRun.objects.get(id=parent)
    except OperatorRun.DoesNotExist:
        operator_run_parent = None

    operator_run = OperatorRun.objects.create(operator=operator.model,
                                              num_total_runs=len(valid_jobs),
                                              job_group=jg,
                                              job_group_notifier=jgn,
                                              parent=operator_run_parent)
    run_ids = []
    pipeline_id = None

    try:
        pipeline_id = operator.get_pipeline_id()
        p = Pipeline.objects.get(id=pipeline_id)
        pipeline_name = p.name
        pipeline_version = p.version
        pipeline_link = p.pipeline_link
    except Pipeline.DoesNotExist:
        pipeline_name = ""
        pipeline_link = ""
        pipeline_version = ""

    pipeline_description_event = AddPipelineToDescriptionEvent(job_group_notifier_id, pipeline_name,
                                                               pipeline_version,
                                                               pipeline_link).to_dict()
    send_notification.delay(pipeline_description_event)

    set_pipeline_field = SetPipelineFieldEvent(job_group_notifier_id, pipeline_name).to_dict()
    send_notification.delay(set_pipeline_field)

    for job in valid_jobs:
        logger.info("Creating Run object")
        run = job[0].save(operator_run_id=operator_run.id, job_group_id=job_group_id,
                          job_group_notifier_id=job_group_notifier_id)
        logger.info("Run object created with id: %s" % str(run.id))
        run_ids.append({"run_id": str(run.id), 'tags': run.tags, 'output_directory': run.output_directory})
        output_directory = run.output_directory
        if not pipeline_name and not pipeline_link:
            logger.info("Run [ id: %s ] failed as the pipeline [ id: %s ] was not found", run.id, pipeline_id)
            error_message = dict(details="Pipeline [ id: %s ] was not found.".format(pipeline_id))
            fail_job(run.id, error_message)
        else:
            create_run_task.delay(str(run.id), job[1], output_directory)

    if job_group_id:
        event = OperatorRunEvent(job_group_notifier_id,
                                 operator.request_id,
                                 pipeline_name,
                                 pipeline_link,
                                 run_ids,
                                 str(operator_run.id)).to_dict()
        send_notification.delay(event)

    for job in invalid_jobs:
        # TODO: Report this to JIRA ticket also
        logger.error("Job invalid: %s" % str(job[0].errors))

    operator_run.status = RunStatus.RUNNING
    operator_run.save()


@shared_task
def create_jobs_from_request(request_id, operator_id, job_group_id, job_group_notifier_id=None, pipeline=None):
    logger.info("Creating operator id %s for requestId: %s for job_group: %s" % (operator_id, request_id, job_group_id))
    operator_model = Operator.objects.get(id=operator_id)

    if not job_group_notifier_id:
        try:
            job_group = JobGroup.objects.get(id=job_group_id)
        except JobGroup.DoesNotExist:
            raise Exception("JobGroup doesn't exist")
        try:
            job_group_notifier_id = notifier_start(job_group, request_id, operator=operator_model)
        except Exception as e:
            logger.error("Failed to instantiate Notifier: %s" % str(e))

    operator = OperatorFactory.get_by_model(operator_model,
                                            job_group_id=job_group_id,
                                            job_group_notifier_id=job_group_notifier_id,
                                            request_id=request_id,
                                            pipeline=pipeline)

    _set_link_to_run_ticket(request_id, job_group_notifier_id)

    generate_description(job_group_id, job_group_notifier_id, request_id)
    generate_label(job_group_notifier_id, request_id)
    create_jobs_from_operator(operator, job_group_id, job_group_notifier_id)


def _set_link_to_run_ticket(request_id, job_group_notifier_id):
    jira_id = None
    import_job = Job.objects.filter(run=TYPES['REQUEST'], args__request_id=request_id).order_by('-created_date').first()
    if not import_job:
        logger.error("Could not find Import JIRA ticket")
        return
    try:
        job_group_notifier_job = JobGroupNotifier.objects.get(job_group=import_job.job_group.id, notifier_type__default=True)
    except JobGroupNotifier.DoesNotExist:
        logger.error("Could not find Import JIRA ticket")
        return
    try:
        new_jira = JobGroupNotifier.objects.get(id=job_group_notifier_id)
    except JobGroupNotifier.DoesNotExist:
        logger.error("Could not find Import JIRA ticket")
        return
    event = SetRunTicketInImportEvent(job_notifier=str(job_group_notifier_job.id), run_jira_id=new_jira.jira_id).to_dict()
    send_notification.delay(event)


def _generate_summary(req):
    approx_create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = req + " [%s]" % approx_create_time
    return summary


def generate_description(job_group, job_group_notifier, request):
    files = FileRepository.filter(metadata={'requestId': request, 'igocomplete': True})
    if files:
        data = files.first().metadata
        request_id = data['requestId']
        recipe = data['recipe']
        a_name = data['dataAnalystName']
        a_email = data['dataAnalystEmail']
        i_name = data['investigatorName']
        i_email = data['investigatorEmail']
        l_name = data['labHeadName']
        l_email = data['labHeadEmail']
        p_email = data['piEmail']
        pm_name = data['projectManagerName']
        qc_emails = data['qcAccessEmails']
        num_samples = len(files.order_by().values('metadata__cmoSampleName').annotate(n=Count("pk")))
        num_tumors = len(FileRepository.filter(queryset=files, metadata={'tumorOrNormal': 'Tumor'}).order_by().values(
                'metadata__cmoSampleName').annotate(n=Count("pk")))
        num_normals = len(FileRepository.filter(queryset=files, metadata={'tumorOrNormal': 'Normal'}).order_by().values(
                'metadata__cmoSampleName').annotate(n=Count("pk")))
        operator_start_event = OperatorStartEvent(job_group_notifier, job_group, request_id, num_samples, recipe, a_name, a_email, i_name, i_email, l_name, l_email, p_email, pm_name, qc_emails, num_tumors, num_normals).to_dict()
        send_notification.delay(operator_start_event)


def generate_label(job_group_id, request):
    files = FileRepository.filter(metadata={'requestId': request, 'igocomplete': True})
    if files:
        data = files.first().metadata
        recipe = data['recipe']
        recipe_label_event = SetLabelEvent(job_group_id, recipe).to_dict()
        send_notification.delay(recipe_label_event)


@shared_task
def create_jobs_from_chaining(to_operator_id, from_operator_id, run_ids=[], job_group_id=None,
                              job_group_notifier_id=None, parent=None):
    logger.info("Creating operator id %s from chaining: %s" % (to_operator_id, from_operator_id))
    operator_model = Operator.objects.get(id=to_operator_id)
    operator = OperatorFactory.get_by_model(operator_model, job_group_id=job_group_id,
                                            job_group_notifier_id=job_group_notifier_id, run_ids=run_ids)
    create_jobs_from_operator(operator, job_group_id, job_group_notifier_id, parent)


@shared_task
def process_triggers():
    operator_runs = OperatorRun.objects.prefetch_related(
        'runs', 'operator__from_triggers'
    ).exclude(status__in=[RunStatus.COMPLETED, RunStatus.FAILED])

    for operator_run in operator_runs:
        created_chained_job = False
        job_group = operator_run.job_group
        job_group_id = str(job_group.id) if job_group else None
        job_group_notifier = operator_run.job_group_notifier
        job_group_notifier_id = str(job_group_notifier.id) if job_group_notifier else None
        try:
            for trigger in operator_run.operator.from_triggers.all():
                trigger_type = trigger.run_type

                if trigger_type == TriggerRunType.AGGREGATE:
                    condition = trigger.aggregate_condition
                    if condition == TriggerAggregateConditionType.ALL_RUNS_SUCCEEDED:
                        if operator_run.percent_runs_succeeded == 100.0:
                            created_chained_job = True
                            create_jobs_from_chaining.delay(
                                trigger.to_operator_id,
                                trigger.from_operator_id,
                                list(operator_run.runs.order_by('id').values_list('id', flat=True)),
                                job_group_id=job_group_id,
                                job_group_notifier_id=job_group_notifier_id,
                                parent=str(operator_run.id)
                            )
                            continue
                    elif condition == TriggerAggregateConditionType.NINTY_PERCENT_SUCCEEDED:
                        if operator_run.percent_runs_succeeded >= 90.0:
                            created_chained_job = True
                            create_jobs_from_chaining.delay(
                                trigger.to_operator_id,
                                trigger.from_operator_id,
                                list(operator_run.runs.order_by('id').values_list('id', flat=True)),
                                job_group_id=job_group_id,
                                job_group_notifier_id=job_group_notifier_id,
                                parent=str(operator_run.id)
                            )
                            continue

                    if operator_run.percent_runs_finished == 100.0:
                        logger.info("Condition never met for operator run %s" % operator_run.id)

                elif trigger_type == TriggerRunType.INDIVIDUAL:
                    if operator_run.percent_runs_finished == 100.0:
                        operator_run.complete()

            if operator_run.percent_runs_finished == 100.0:
                if operator_run.percent_runs_succeeded == 100.0:
                    operator_run.complete()
                    if not created_chained_job and job_group_notifier_id:
                        completed_event = SetPipelineCompletedEvent(job_group_notifier_id).to_dict()
                        send_notification.delay(completed_event)
                else:
                    operator_run.fail()
                    if job_group_notifier_id:
                        e = OperatorRequestEvent(job_group_notifier_id, "[CIReviewEvent] Operator Run %s failed" % str(operator_run.id)).to_dict()
                        send_notification.delay(e)
                        ci_review_event = SetCIReviewEvent(job_group_notifier_id).to_dict()
                        send_notification.delay(ci_review_event)

        except Exception as e:
            logger.info("Trigger %s Fail. Error %s" % (operator_run.id, str(e)))
            operator_run.fail()


def on_failure_to_create_run_task(self, exc, task_id, args, kwargs, einfo):
    run_id = args[0]
    fail_job(run_id, "Could not create run task")

@shared_task(autoretry_for=(Exception,),
             retry_jitter=True,
             retry_backoff=60,
             retry_kwargs={"max_retries": 4},
             on_failure=on_failure_to_create_run_task)
def create_run_task(run_id, inputs, output_directory=None):
    logger.info("Creating and validating Run for %s" % run_id)
    try:
        run = RunObject.from_cwl_definition(run_id, inputs)
        run.ready()
    except RunCreateException as e:
        run = RunObject.from_db(run_id)
        run.fail({'details': str(e)})
        RunObject.to_db(run)
        logger.info("Run %s Failed" % run_id)
    else:
        RunObject.to_db(run)
        submit_job.delay(run_id, output_directory)
        logger.info("Run %s Ready" % run_id)


def on_failure_to_submit_job(self, exc, task_id, args, kwargs, einfo):
    run_id = args[0]

    fail_job(run_id, "Failed to submit job to Ridgeback")

@shared_task(autoretry_for=(Exception,),
             retry_jitter=True,
             retry_backoff=60,
             retry_kwargs={"max_retries": 4},
             on_failure=on_failure_to_submit_job)
def submit_job(run_id, output_directory=None):
    resume = None
    try:
        run = Run.objects.get(id=run_id)
    except Run.DoesNotExist:
        raise Exception("Failed to submit a run")

    if run.resume:
        run1 = RunObject.from_db(run_id)
        run2 = RunObject.from_db(run.resume)

        if run1.equal(run2):
            logger.info("Resuming run: %s with execution id: %s" % (str(run.resume), str(run2.run_obj.execution_id)))
            resume = str(run2.run_obj.execution_id)
        else:
            logger.info("Failed to resume runs not equal")
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
    logger.info("Job %s ready for submitting" % run_id)
    if resume:
        url = urljoin(settings.RIDGEBACK_URL, '/v0/jobs/{id}/resume/'.format(
            id=resume))
        job = {
            'root_dir': output_directory
        }
        response = requests.post(url, json=job)
    else:
        url = settings.RIDGEBACK_URL + '/v0/jobs/'
        job = {
            'app': app,
            'inputs': inputs,
            'root_dir': output_directory
        }
        response = requests.post(url, json=job)
    if response.status_code == 201:
        run.execution_id = response.json()['id']
        run.status = RunStatus.RUNNING
        logger.info("Job %s successfully submitted with id:%s" % (run_id, run.execution_id))
        run.save()
    else:
        raise Exception("Failed to submit job %s" % run_id)

@shared_task
def abort_job_task(job_group_id=None, jobs=[]):
    successful = []
    unsuccessful = []
    runs = []
    if job_group_id:
        runs = list(Run.objects.filter(job_group_id=job_group_id).all())
        runs = [str(run.execution_id) for run in runs]
    for j in jobs:
        run_obj = Run.objects.get(id=j)
        if str(run_obj.execution_id) not in runs:
            runs.append(str(run_obj.execution_id))
    for run in runs:
        if abort_job_on_ridgeback(run):
            successful.append(run)
        else:
            unsuccessful.append(run)
    if unsuccessful:
        logger.error("Failed to abort %s" % ', '.join(unsuccessful))


def abort_job_on_ridgeback(job_id):
    response = requests.get(settings.RIDGEBACK_URL + '/v0/jobs/%s/abort/' % job_id)
    if response.status_code == 200:
        logger.info("Job %s aborted" % job_id)
        return True
    logger.error("Failed to abort job: %s" % job_id)
    return None


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

    job_group_notifier = run.job_group_notifier
    job_group_notifier_id = str(job_group_notifier.id) if job_group_notifier else None

    ci_review = SetCIReviewEvent(job_group_notifier_id).to_dict()
    send_notification.delay(ci_review)

    _job_finished_notify(run)


def complete_job(run_id, outputs):
    run = RunObject.from_db(run_id)
    if run.run_obj.is_completed:
        return

    try:
        run.complete(outputs)
    except Exception as e:
        fail_job(run_id, str(e))
        return

    run.to_db()
    job_group = run.job_group
    job_group_id = str(job_group.id) if job_group else None

    _job_finished_notify(run)

    for trigger in run.run_obj.operator_run.operator.from_triggers.filter(run_type=TriggerRunType.INDIVIDUAL):
        create_jobs_from_chaining.delay(
            trigger.to_operator_id,
            trigger.from_operator_id,
            [run_id],
            job_group_id=job_group_id,
            parent=str(run.run_obj.operator_run.id) if run.run_obj.operator_run else None
        )


def _job_finished_notify(run):
    job_group_notifier = run.job_group_notifier
    job_group_notifier_id = str(job_group_notifier.id) if job_group_notifier else None

    pipeline_name = run.run_obj.app.name
    pipeline_link = run.run_obj.app.pipeline_link

    if run.run_obj.operator_run:
        operator_run_id = str(run.run_obj.operator_run.id)
        total_runs = run.run_obj.operator_run.total_runs
        completed_runs = run.run_obj.operator_run.completed_runs
        failed_runs = run.run_obj.operator_run.failed_runs
        running_runs = run.run_obj.operator_run.running_runs
    else:
        operator_run_id = None
        total_runs = 1
        if run.status == RunStatus.COMPLETED:
            completed_runs, failed_runs = 1, 0
        else:
            completed_runs, failed_runs = 0, 1
        running_runs = 0

    event = RunFinishedEvent(job_group_notifier_id,
                             run.tags.get('requestId', 'UNKNOWN REQUEST'),
                             str(run.run_id),
                             pipeline_name,
                             pipeline_link,
                             run.run_obj.output_directory,
                             RunStatus(run.status).name,
                             run.tags,
                             running_runs,
                             completed_runs,
                             failed_runs,
                             total_runs,
                             operator_run_id
                             )
    e = event.to_dict()
    send_notification.delay(e)


def running_job(run):
    run.status = RunStatus.RUNNING
    run.save()


def abort_job(run):
    run.status = RunStatus.ABORTED
    run.save()

def update_commandline_job_status(run, commandline_tool_job_set):
    job_status_obj = {}
    for single_commandline_job in commandline_tool_job_set:
        status = single_commandline_job.pop('status')
        root = single_commandline_job.pop('root')
        if status not in job_status_obj:
            job_status_obj[status] = []
        job_status_obj[status].append(single_commandline_job)

    run.job_statuses = job_status_obj
    run.save()


@shared_task
def check_jobs_status():
    runs = Run.objects.filter(status__in=(RunStatus.RUNNING, RunStatus.READY)).all()
    for run in runs:
        if run.execution_id:
            logger.info("Checking status for job: %s [%s]" % (run.id, run.execution_id))
            remote_status = check_status_on_ridgeback(run.execution_id)
            if remote_status:
                if remote_status['commandlinetooljob_set']:
                    update_commandline_job_status(run, remote_status['commandlinetooljob_set'])
                if remote_status['status'] == 'FAILED':
                    logger.info("Job %s [%s] FAILED" % (run.id, run.execution_id))
                    message = dict(details=remote_status.get('message'))
                    fail_job(str(run.id),
                             message)
                    continue
                if remote_status['status'] == 'COMPLETED':
                    logger.info("Job %s [%s] COMPLETED" % (run.id, run.execution_id))
                    complete_job(str(run.id), remote_status['outputs'])
                    continue
                if remote_status['status'] == 'CREATED' or remote_status['status'] == 'PENDING' or remote_status['status'] == 'RUNNING':
                    logger.info("Job %s [%s] RUNNING" % (run.id, run.execution_id))
                    running_job(run)
                    continue
                if remote_status['status'] == 'ABORTED':
                    logger.info("Job %s [%s] ABORTED" % (run.id, run.execution_id))
                    abort_job(run)
            else:
                logger.error("Failed to check status for job: %s [%s]" % (run.id, run.execution_id))
        else:
            logger.error("Job %s not submitted" % str(run.id))


def run_routine_operator_job(operator, job_group_id=None):
    """
    Bit of a workaround.

    Only runs the get_jobs() function of the given operator; does not expect any pipeline runs.
    """
    job = operator.get_jobs()
    logger.info("Running single operator job; no pipeline runs submitted.")


def create_aion_job(operator, lab_head_email, job_group_id=None, job_group_notifier_id=None):
    jobs = operator.get_jobs(lab_head_email)
    create_operator_run_from_jobs(operator, jobs, job_group_id, job_group_notifier_id)


def create_tempo_mpgen_job(operator, pairing_override=None, job_group_id=None, job_group_notifier_id=None):
    jobs = operator.get_jobs(pairing_override)
    create_operator_run_from_jobs(operator, jobs, job_group_id, job_group_notifier_id)
