import os
import logging
import requests
import traceback
from datetime import datetime, timedelta
from lib.memcache_lock import memcache_lock
from urllib.parse import urljoin
from celery import shared_task
from django.conf import settings
from django.db.models import Count
from runner.run.objects.run_object_factory import RunObjectFactory
from .models import Run, RunStatus, OperatorRun, TriggerAggregateConditionType, TriggerRunType, Pipeline
from notifier.events import (
    RunFinishedEvent,
    OperatorRequestEvent,
    OperatorRunEvent,
    SetCIReviewEvent,
    SetPipelineCompletedEvent,
    AddPipelineToDescriptionEvent,
    SetPipelineFieldEvent,
    OperatorStartEvent,
    SetLabelEvent,
    SetDeliveryDateFieldEvent,
    VoyagerActionRequiredForRunningEvent,
    SendEmailEvent,
    OperatorErrorEvent,
)
from notifier.tasks import send_notification, notifier_start
from runner.operator import OperatorFactory
from beagle_etl.models import Operator
from beagle_etl.jobs.notification_helper import _voyager_start_processing
from notifier.models import JobGroup, JobGroupNotifier
from notifier.helper import get_emails_to_notify, get_gene_panel, get_samples
from file_system.models import Request
from file_system.repository import FileRepository
from runner.cache.github_cache import GithubCache
from lib.logger import format_log
from lib.memcache_lock import memcache_task_lock
from study.objects import StudyObject
from study.models import JobGroupWatcher, JobGroupWatcherConfig
from ddtrace import tracer

logger = logging.getLogger("django")


def create_jobs_from_operator(operator, job_group_id=None, job_group_notifier_id=None, parent=None, notify=False):
    try:
        jobs = operator.get_jobs()
        if operator.logger.message:
            event = OperatorErrorEvent(job_group_notifier_id, operator.logger.message)
            send_notification.delay(event.to_dict())
    except Exception as e:
        logger.error(f"Exception in Operator get_jobs for: {operator}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        gene_panel = get_gene_panel(operator.request_id)
        number_of_samples = get_samples(operator.request_id).count()
        send_to = get_emails_to_notify(operator.request_id, "VoyagerActionRequiredForRunningEvent")
        for email in send_to:
            event = VoyagerActionRequiredForRunningEvent(
                job_notifier=settings.BEAGLE_NOTIFIER_EMAIL_GROUP,
                email_to=email,
                email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM,
                subject=f"Action Required for Project {operator.request_id}",
                request_id=operator.request_id,
                gene_panel=gene_panel,
                number_of_samples=number_of_samples,
            ).to_dict()
            send_notification.delay(event)
        logger.info(
            format_log("Operator get_jobs failed %s", str(e), job_group_id=job_group_id, request_id=operator.request_id)
        )
    else:
        create_operator_run_from_jobs(operator, jobs, job_group_id, job_group_notifier_id, parent, notify=notify)


def create_operator_run_from_jobs(
    operator, jobs, job_group_id=None, job_group_notifier_id=None, parent=None, notify=False
):
    jg = None
    jgn = None

    if not jobs:
        logger.info("Could not create operator run due to no jobs being passed")
        return

    try:
        jg = JobGroup.objects.get(id=job_group_id)
    except JobGroup.DoesNotExist:
        logger.info(format_log("Job group not set", job_group_id=job_group_id))
    try:
        jgn = JobGroupNotifier.objects.get(id=job_group_notifier_id)
    except JobGroupNotifier.DoesNotExist:
        logger.info(format_log("Job group notifier not set", job_group_id=job_group_id))
    valid_jobs, invalid_jobs = [], []

    for job in jobs:
        valid_jobs.append(job) if job.is_valid() else invalid_jobs.append(job)

    try:
        operator_run_parent = OperatorRun.objects.get(id=parent)
    except OperatorRun.DoesNotExist:
        operator_run_parent = None

    operator_run = OperatorRun.objects.create(
        operator=operator.model,
        num_total_runs=len(valid_jobs),
        job_group=jg,
        job_group_notifier=jgn,
        parent=operator_run_parent,
    )

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

    pipeline_description_event = AddPipelineToDescriptionEvent(
        job_group_notifier_id, pipeline_name, pipeline_version, pipeline_link
    ).to_dict()
    send_notification.delay(pipeline_description_event)

    set_pipeline_field = SetPipelineFieldEvent(job_group_notifier_id, pipeline_name).to_dict()
    send_notification.delay(set_pipeline_field)

    for job in valid_jobs:
        logger.info(format_log("Creating run", obj=job))
        job.operator_run_id = str(operator_run.id)
        job.job_group_id = str(job_group_id) if job_group_id else job_group_id
        job.job_group_notifier_id = str(job_group_notifier_id) if job_group_notifier_id else job_group_notifier_id
        run = job.create()
        logger.info(format_log("Run created", obj=run))

        run_ids.append({"run_id": str(run.id), "tags": run.tags, "output_directory": run.output_directory})
        output_directory = run.output_directory
        if not pipeline_name and not pipeline_link:
            logger.error(
                format_log(
                    "Run failed, could not find pipeline %s" % pipeline_id,
                    obj=run,
                    job_group_id=job_group_id,
                    operator_run_id=operator_run.id,
                )
            )
            error_message = dict(details="Pipeline [ id: %s ] was not found.".format(pipeline_id))
            fail_job(run.id, error_message)
        else:
            create_run_task.delay(str(run.id), job.inputs, output_directory)

    if job_group_id:
        event = OperatorRunEvent(
            job_group_notifier_id, operator.request_id, pipeline_name, pipeline_link, run_ids, str(operator_run.id)
        ).to_dict()
        send_notification.delay(event)

    for job in invalid_jobs:
        # TODO: Report this to JIRA ticket also
        logger.error(
            format_log(
                "Job invalid %s" % job.errors, obj=job, job_group_id=job_group_id, operator_run_id=operator_run.id
            )
        )
        logger.error(
            format_log(
                "Job invalid %s" % job[0].errors, obj=job[0], job_group_id=job_group_id, operator_run_id=operator_run.id
            )
        )

    if not operator_run_parent:
        _voyager_start_processing(request_id=operator.request_id, run_ids=[r["run_id"] for r in run_ids], notify=notify)

    operator_run.status = RunStatus.RUNNING
    operator_run.save()


@shared_task
@tracer.wrap(service="beagle")
def create_jobs_from_request(
    request_id, operator_id, job_group_id, job_group_notifier_id=None, pipeline=None, file_group=None, notify=False
):
    current_span = tracer.current_span()
    current_span.set_tag("request.id", request_id)

    logger.info(format_log("Creating operator with %s" % operator_id, job_group_id=job_group_id, request_id=request_id))
    operator_model = Operator.objects.get(id=operator_id)

    if not job_group_notifier_id:
        try:
            job_group = JobGroup.objects.get(id=job_group_id)
        except JobGroup.DoesNotExist:
            logger.info(
                format_log("Job group does not exist" % operator_id, job_group_id=job_group_id, request_id=request_id)
            )
            return
        try:
            job_group_notifier_id = notifier_start(job_group, request_id, operator=operator_model)
            request_obj = Request.objects.filter(request_id=request_id).first()
            if request_obj:
                delivery_date_event = SetDeliveryDateFieldEvent(
                    job_group_notifier_id, str(request_obj.delivery_date)
                ).to_dict()
                send_notification.delay(delivery_date_event)
        except Exception as e:
            logger.info(
                format_log(
                    f"Failed to instantiate notifier {operator_id}", job_group_id=job_group_id, request_id=request_id
                )
            )

    studies = StudyObject.get_by_request(request_id)
    postprocessors = JobGroupWatcherConfig.objects.filter(operators=operator_id)
    for study in studies:
        for config in postprocessors:
            JobGroupWatcher.objects.create(study=study.db_object, job_group=job_group, config=config)

    operator = OperatorFactory.get_by_model(
        operator_model,
        job_group_id=job_group_id,
        job_group_notifier_id=job_group_notifier_id,
        request_id=request_id,
        pipeline=pipeline,
        file_group=file_group,
    )
    generate_description(operator, job_group_id, job_group_notifier_id, request_id)
    generate_label(job_group_notifier_id, request_id)
    create_jobs_from_operator(operator, job_group_id, job_group_notifier_id, notify=notify)


@shared_task
def create_jobs_from_pairs(
    pipeline_id,
    pairs,
    name,
    assay,
    investigatorName,
    labHeadName,
    file_group_id,
    job_group_id,
    request_id=None,
    output_directory_prefix=None,
):
    pipeline = Pipeline.objects.get(id=pipeline_id)
    job_group = JobGroup.objects.get(id=job_group_id)

    try:
        job_group_notifier = JobGroupNotifier.objects.get(
            job_group_id=job_group_id, notifier_type_id=pipeline.operator.notifier_id
        )
        job_group_notifier_id = str(job_group_notifier.id)
    except JobGroupNotifier.DoesNotExist:
        metadata = {"assay": assay, "investigatorName": investigatorName, "labHeadName": labHeadName}
        job_group_notifier_id = notifier_start(job_group, name, operator=pipeline.operator, metadata=metadata)

    operator_model = Operator.objects.get(id=pipeline.operator_id)
    operator = OperatorFactory.get_by_model(
        operator_model,
        pairing={"pairs": pairs},
        job_group_id=job_group_id,
        job_group_notifier_id=job_group_notifier_id,
        request_id=request_id,
        file_group=file_group_id,
        output_directory_prefix=output_directory_prefix,
    )

    generate_description(operator, job_group_id, job_group_notifier_id, request_id)
    generate_label(job_group_notifier_id, request_id)
    create_jobs_from_operator(operator, job_group_id, job_group_notifier_id=job_group_notifier_id)


def _generate_summary(req):
    approx_create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = req + " [%s]" % approx_create_time
    return summary


def generate_description(operator, job_group, job_group_notifier, request):
    links = operator.links_to_files()
    files = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request, settings.IGO_COMPLETE_METADATA_KEY: True}
    )
    if files:
        data = files.first().metadata
        request_id = data[settings.REQUEST_ID_METADATA_KEY]
        recipe = data[settings.RECIPE_METADATA_KEY]
        a_name = data["dataAnalystName"]
        a_email = data["dataAnalystEmail"]
        i_name = data["investigatorName"]
        i_email = data["investigatorEmail"]
        l_name = data["labHeadName"]
        l_email = data["labHeadEmail"]
        p_email = data["piEmail"]
        pm_name = data["projectManagerName"]
        qc_emails = data["qcAccessEmails"] if "qcAccessEmails" in data else ""
        data_access_emails = data["dataAccessEmails"] if "dataAccessEmails" in data else ""
        other_contact_emails = data["otherContactEmails"] if "otherContactEmails" in data else ""

        num_samples = len(files.order_by().values("metadata__ciTag").annotate(n=Count("pk")))
        num_tumors = len(
            FileRepository.filter(queryset=files, metadata={"tumorOrNormal": "Tumor"})
            .order_by()
            .values("metadata__ciTag")
            .annotate(n=Count("pk"))
        )
        num_normals = len(
            FileRepository.filter(queryset=files, metadata={"tumorOrNormal": "Normal"})
            .order_by()
            .values("metadata__ciTag")
            .annotate(n=Count("pk"))
        )
        operator_start_event = OperatorStartEvent(
            job_group_notifier,
            job_group,
            request_id,
            num_samples,
            recipe,
            a_name,
            a_email,
            i_name,
            i_email,
            l_name,
            l_email,
            p_email,
            pm_name,
            qc_emails,
            num_tumors,
            num_normals,
            data_access_emails,
            other_contact_emails,
            links,
        ).to_dict()
        send_notification.delay(operator_start_event)


def generate_label(job_group_id, request):
    files = FileRepository.filter(
        metadata={settings.REQUEST_ID_METADATA_KEY: request, settings.IGO_COMPLETE_METADATA_KEY: True}
    )
    if files:
        data = files.first().metadata
        recipe = data[settings.RECIPE_METADATA_KEY]
        recipe_label_event = SetLabelEvent(job_group_id, recipe).to_dict()
        send_notification.delay(recipe_label_event)


@shared_task
def create_jobs_from_chaining(
    to_operator_id, from_operator_id, run_ids=[], job_group_id=None, job_group_notifier_id=None, parent=None
):
    logger.info(
        format_log(
            "Creating operator id %s from chaining: %s" % (to_operator_id, from_operator_id), job_group_id=job_group_id
        )
    )
    operator_model = Operator.objects.get(id=to_operator_id)
    operator = OperatorFactory.get_by_model(
        operator_model, job_group_id=job_group_id, job_group_notifier_id=job_group_notifier_id, run_ids=run_ids
    )
    create_jobs_from_operator(operator, job_group_id, job_group_notifier_id, parent)


@shared_task
def process_triggers():
    operator_runs = OperatorRun.objects.prefetch_related("runs", "operator__from_triggers").exclude(
        status__in=[RunStatus.COMPLETED, RunStatus.FAILED]
    )

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
                            run_ids = [
                                str(run_id)
                                for run_id in list(operator_run.runs.order_by("id").values_list("id", flat=True))
                            ]
                            created_chained_job = True
                            create_jobs_from_chaining.delay(
                                trigger.to_operator_id,
                                trigger.from_operator_id,
                                run_ids,
                                job_group_id=job_group_id,
                                job_group_notifier_id=job_group_notifier_id,
                                parent=str(operator_run.id),
                            )
                            continue
                    elif condition == TriggerAggregateConditionType.NINTY_PERCENT_SUCCEEDED:
                        if operator_run.percent_runs_succeeded >= 90.0:
                            created_chained_job = True
                            create_jobs_from_chaining.delay(
                                trigger.to_operator_id,
                                trigger.from_operator_id,
                                list(operator_run.runs.order_by("id").values_list("id", flat=True)),
                                job_group_id=job_group_id,
                                job_group_notifier_id=job_group_notifier_id,
                                parent=str(operator_run.id),
                            )
                            continue

                    if operator_run.percent_runs_finished == 100.0:
                        logger.info(
                            format_log(
                                "Conditions never met", operator_run_id=operator_run.id, job_group_id=job_group_id
                            )
                        )

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
                        e = OperatorRequestEvent(
                            job_group_notifier_id, "[CIReviewEvent] Operator Run %s failed" % str(operator_run.id)
                        ).to_dict()
                        send_notification.delay(e)
                        ci_review_event = SetCIReviewEvent(job_group_notifier_id).to_dict()
                        send_notification.delay(ci_review_event)

        except Exception as e:
            logger.info(
                format_log("Trigger failed %s", str(e), operator_run_id=operator_run.id, job_group_id=job_group_id)
            )
            operator_run.fail()


def on_failure_to_create_run_task(self, exc, task_id, args, kwargs, einfo):
    run_id = args[0]
    fail_job(run_id, "Could not create run task")


@shared_task(
    autoretry_for=(Exception,),
    retry_jitter=True,
    retry_backoff=60,
    retry_kwargs={"max_retries": 4},
    on_failure=on_failure_to_create_run_task,
)
def create_run_task(run_id, inputs, output_directory=None):
    logger.info(format_log("Creating and validating run", obj_id=run_id))
    run = RunObjectFactory.from_definition(run_id, inputs)
    run.ready()
    run.to_db()
    submit_job.delay(run_id, output_directory)
    logger.info(format_log("Run is ready", obj=run))


def on_failure_to_submit_job(self, exc, task_id, args, kwargs, einfo):
    run_id = args[0]
    fail_job(run_id, "Failed to submit job to Ridgeback")


@shared_task(
    autoretry_for=(Exception,),
    retry_jitter=True,
    retry_backoff=60,
    retry_kwargs={"max_retries": 4},
    on_failure=on_failure_to_submit_job,
)
def submit_job(run_id, output_directory=None, execution_id=None):
    resume = None
    try:
        run = Run.objects.get(id=run_id)
    except Run.DoesNotExist:
        raise Exception("Failed to submit a run")

    run1 = RunObjectFactory.from_db(run_id)
    if run.resume:
        run2 = RunObjectFactory.from_db(run.resume)

        if run1.equal(run2):
            logger.info(format_log("Resuming run with execution id %s" % run2.run_obj.execution_id, obj=run))
            resume = str(run2.run_obj.execution_id)
        else:
            logger.info(
                format_log("Failed to resume runs as run is not equal to the following run: %s" % str(run2), obj=run)
            )
    if execution_id:
        resume = execution_id
    if not output_directory:
        output_directory = os.path.join(run.app.output_directory, str(run_id))
    job = run1.dump_job(output_directory=output_directory)
    logger.info(format_log("Log output directory {path}".format(path=run1.run_obj.log_directory), obj=run1))
    logger.info(format_log("Job ready for submitting", obj=run1))
    if resume:
        url = urljoin(settings.RIDGEBACK_URL, "/v0/jobs/{id}/resume/".format(id=resume))
        job = {"root_dir": output_directory, "base_dir": run.app.output_directory}
    else:
        url = settings.RIDGEBACK_URL + "/v0/jobs/"
    if run.app.walltime:
        job["walltime"] = run.app.walltime
    if run.app.tool_walltime:
        job["tool_walltime"] = run.app.tool_walltime
    if run.app.memlimit:
        job["memlimit"] = run.app.memlimit

    root_permissions = run.app.output_permission if run.app.output_permission else settings.DEFAULT_OUTPUTS_PERMISSIONS
    output_uid = run.app.output_uid if run.app.output_uid else settings.DEFAULT_OUTPUTS_UID
    output_gid = run.app.output_gid if run.app.output_gid else settings.DEFAULT_OUTPUTS_GID
    job["root_permission"] = root_permissions
    job["output_uid"] = output_uid
    job["output_gid"] = output_gid
    job["user"] = run.app.user
    job["metadata"] = dict()
    job["metadata"]["run_id"] = str(run_id)
    job["metadata"]["pipeline_id"] = str(run.app.id)
    job["metadata"][
        "pipeline_link"
    ] = f"{run1.run_obj.app.github}/blob/{run1.run_obj.app.version}/{run1.run_obj.app.entrypoint}"
    job["metadata"]["job_group"] = str(run.job_group.id)
    if run.app.pipeline_name:
        job["metadata"]["pipeline_name"] = run.app.pipeline_name.name
    else:
        job["metadata"]["pipeline_name"] = "NA"

    response = requests.post(url, json=job)
    if response.status_code == 201:
        run.execution_id = response.json()["id"]
        logger.info(format_log("Job successfully submitted", obj=run))
        run.save()
    else:
        raise Exception("Failed to submit job %s" % run_id)


@shared_task
def terminate_job_task(job_group_id=None, jobs=[]):
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
        if terminate_job_on_ridgeback(run):
            successful.append(run)
        else:
            unsuccessful.append(run)
    if unsuccessful:
        logger.error("Failed to terminate %s" % ", ".join(unsuccessful))


def terminate_job_on_ridgeback(job_id):
    response = requests.get(settings.RIDGEBACK_URL + "/v0/jobs/%s/terminate/" % job_id)
    if response.status_code == 200:
        logger.info(format_log("Job terminated", obj_id=job_id))
        return True
    logger.error(format_log("Failed to terminate job", obj_id=job_id))
    return None


def check_statuses_on_ridgeback(execution_ids):
    response = requests.post(settings.RIDGEBACK_URL + "/v0/jobs/statuses/", data={"job_ids": execution_ids})
    if response.status_code == 200:
        logger.info("Job statuses checked")
        return response.json()["jobs"]
    logger.error("Failed to fetch job statuses with status code: %s" % response.status_code)
    return None


@shared_task(bind=True)
def fail_job(self, run_id, error_message, run_log_location=None, input_json_location=None):
    lock_id = "run_lock_%s" % run_id
    with memcache_task_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            run = RunObjectFactory.from_db(run_id)
            if run.run_obj.is_failed:
                logger.info(format_log("Run Fail already processed", obj=run.run_obj))
                return

            restart_run = run.run_obj.set_for_restart()

            if not restart_run:
                if isinstance(error_message, dict):
                    run.fail(error_message)
                else:
                    run.fail({"Error": str(error_message)})
                run.to_db()

                job_group_notifier = run.job_group_notifier
                job_group_notifier_id = str(job_group_notifier.id) if job_group_notifier else None

                ci_review = SetCIReviewEvent(job_group_notifier_id).to_dict()
                send_notification.delay(ci_review)

                _upload_qc_report(run.run_obj)
                _job_finished_notify(run, run_log_location, input_json_location)
            else:
                run_id, output_directory, execution_id = restart_run
                submit_job.delay(run_id, output_directory, execution_id)
        else:
            logger.warning("Run %s is processing by another worker" % run_id)


@shared_task(bind=True)
def complete_job(self, run_id, outputs, run_log_location=None, inputs_json_location=None):
    lock_id = "run_lock_%s" % run_id
    with memcache_task_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            run = RunObjectFactory.from_db(run_id)
            if run.run_obj.is_completed:
                logger.info(format_log("Run Complete already processed", obj=run.run_obj))
                return

            logger.info(format_log("Completing Run", obj=run.run_obj))

            try:
                run.complete(outputs)
            except Exception as e:
                fail_job(run_id, str(e))
                return

            run.to_db()
            job_group = run.job_group
            job_group_id = str(job_group.id) if job_group else None

            _job_finished_notify(run, run_log_location, inputs_json_location)

            for trigger in run.run_obj.operator_run.operator.from_triggers.filter(run_type=TriggerRunType.INDIVIDUAL):
                create_jobs_from_chaining.delay(
                    trigger.to_operator_id,
                    trigger.from_operator_id,
                    [run_id],
                    job_group_id=job_group_id,
                    parent=str(run.run_obj.operator_run.id) if run.run_obj.operator_run else None,
                )
        else:
            logger.warning("Run %s is processing by another worker" % run_id)


def _upload_qc_report(run):
    operator = OperatorFactory.get_by_model(
        run.operator_run.operator, job_group_id=run.job_group_id, job_group_notifier_id=run.job_group_notifier_id
    )
    try:
        operator.on_job_fail(run)
    except Exception as e:
        logger.error("Operator on_job_fail failed", e)


def _job_finished_notify(run, run_log_location=None, input_json_location=None):
    job_group_notifier = run.job_group_notifier
    job_group_notifier_id = str(job_group_notifier.id) if job_group_notifier else None

    pipeline_name = run.run_obj.app.name
    pipeline_version = run.run_obj.app.version
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

    request_id = "UNKNOWN REQUEST"
    for sample in run.samples:
        tumor_or_normal = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: sample.sample_id},
            values_metadata=settings.TUMOR_OR_NORMAL_METADATA_KEY,
        ).first()

        if tumor_or_normal == "Tumor":
            request_id = FileRepository.filter(
                metadata={settings.SAMPLE_ID_METADATA_KEY: sample.sample_id},
                values_metadata=settings.REQUEST_ID_METADATA_KEY,
            ).first()
            break

    event = RunFinishedEvent(
        job_group_notifier_id,
        request_id,
        str(run.run_id),
        pipeline_name,
        pipeline_version,
        pipeline_link,
        run.run_obj.output_directory,
        RunStatus(run.status).name,
        run.tags,
        running_runs,
        completed_runs,
        failed_runs,
        total_runs,
        operator_run_id,
        run_log_location,
        input_json_location,
        str(run.run_obj.job_group.id),
    )
    e = event.to_dict()
    send_notification.delay(e)


@shared_task(bind=True)
def running_job(self, run_id):
    lock_id = "run_lock_%s" % run_id
    with memcache_task_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            run = Run.objects.get(id=run_id)
            logger.info(format_log("Transition to state RUNNING", obj=run))
            if run.status != RunStatus.RUNNING:
                run.status = RunStatus.RUNNING
                run.save()
        else:
            logger.warning("Run %s is processing by another worker" % run_id)


@shared_task(bind=True)
def terminate_job(self, run_id, run_log_location, inputs_json_location):
    lock_id = "run_lock_%s" % run_id
    with memcache_task_lock(lock_id, self.app.oid) as acquired:
        if acquired:
            run = Run.objects.get(id=run_id)
            logger.info(format_log("Transition to state TERMINATED", obj=run))
            if run.status != RunStatus.TERMINATED:
                run.status = RunStatus.TERMINATED
                run.save()
                run_obj = RunObjectFactory.from_db(run_id)
                _job_finished_notify(run_obj, run_log_location, inputs_json_location)
        else:
            logger.warning("Run %s is processing by another worker" % run_id)


def update_commandline_job_status(run, commandline_tool_job_set):
    job_status_obj = {}
    for single_commandline_job in commandline_tool_job_set:
        status = single_commandline_job.pop("status")
        root = single_commandline_job.pop("root")
        if status not in job_status_obj:
            job_status_obj[status] = []
        job_status_obj[status].append(single_commandline_job)
    run.job_statuses = job_status_obj


@shared_task
def check_job_timeouts():
    TIMEOUT_BY_DAYS = 3
    diff = datetime.now() - timedelta(days=TIMEOUT_BY_DAYS)
    runs = Run.objects.filter(
        status__in=(RunStatus.CREATING, RunStatus.READY), created_date__lte=diff, execution_id__isnull=True
    ).all()

    for run in runs:
        fail_job(run.id, "Run timedout after %s days" % TIMEOUT_BY_DAYS)


def send_hanging_job_alert(run_id, message):
    for email in settings.JOB_HANGING_ALERT_EMAILS:
        content = f"""Run {settings.BEAGLE_URL}/v0/run/api/{run_id}/ possible hanging.
        
                      {message}"""
        email = SendEmailEvent(
            job_notifier=settings.BEAGLE_NOTIFIER_EMAIL_GROUP,
            email_to=email,
            email_from=settings.BEAGLE_NOTIFIER_EMAIL_FROM,
            subject=f"ALERT: Hanging job detected {settings.BEAGLE_URL}/v0/run/api/{run_id}/",
            content=content,
        )
        send_notification.delay(email.to_dict())


@shared_task
@memcache_lock("check_operator_run_alerts")
def check_operator_run_alerts():
    def _create_sample_str(single_run):
        samples_str = "NA"
        if single_run.samples:
            samples = []
            for single_sample in single_run.samples.all():
                samples.append(single_sample.sample_id)
            samples_str = ", ".join(samples)
        return samples_str

    triggered_operator_runs = (
        OperatorRun.objects.all()
        .prefetch_related("runs", "job_group_notifier")
        .filter(num_manual_restarts__gte=settings.MANUAL_RESTART_REPORT_THRESHOLD, triggered_alert=False)
    )
    for single_operator_run in triggered_operator_runs:
        failed_runs = (
            single_operator_run.runs.filter(status=RunStatus.FAILED)
            .prefetch_related("app", "samples")
            .order_by("-started")
        )
        completed_dict = {}
        error_dict = {}
        completed_runs = single_operator_run.runs.filter(status=RunStatus.COMPLETED).prefetch_related("app", "samples")
        for single_run in completed_runs:
            samples_str = _create_sample_str(single_run)
            pipeline = single_run.app.name
            finished = single_run.finished_date
            completed_dict[(samples_str, pipeline)] = finished
        if single_operator_run.job_group_notifier:
            requestID = single_operator_run.job_group_notifier.request_id
        else:
            requestID = "NA"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        num_manual_restarts_str = str(single_operator_run.num_manual_restarts)
        alert_message = "-------------- Manual Restart Alert for {} on {} after {} restarts --------------\n".format(
            requestID, current_time, num_manual_restarts_str
        )
        run_info = []
        counter = 1
        for single_run in failed_runs:
            if not single_run.started:
                started = single_run.created_date
            else:
                started = single_run.started
            finished = single_run.finished_date
            delta = finished - started
            delta_seconds = delta.total_seconds()
            delta_hours = divmod(delta_seconds, 3600)[0]
            started_str = started.strftime("%Y-%m-%d %H:%M:%S")
            finished_str = finished.strftime("%Y-%m-%d %H:%M:%S")
            run_name = single_run.name
            pipeline = single_run.app.name
            message = single_run.message
            log_file = "NA"
            failed_jobs = []
            samples_str = _create_sample_str(single_run)
            run_key = (samples_str, pipeline)
            if run_key in completed_dict:
                if completed_dict[run_key] > started:
                    continue
            if run_key in error_dict:
                continue
            else:
                error_dict[run_key] = finished
            if "details" in message:
                if "log" in message["details"]:
                    log_file = message["details"]["log"]
                if "failed_jobs" in message["details"]:
                    for single_tool in message["details"]["failed_jobs"].keys():
                        if single_tool not in failed_jobs:
                            failed_jobs.append(single_tool)
            run_message_line = "{}. Name: Run {}\n".format(str(counter), run_name)
            run_message_line += "Sample: {}\n".format(samples_str)
            run_message_line += "Pipeline: {}\n".format(pipeline)
            run_message_line += "Started: {}, Failed: {}, Total time: {} hour(s)\n".format(
                started_str, finished_str, delta_hours
            )
            run_message_line += "Log_file: {}\n".format(log_file)
            if failed_jobs:
                run_message_line += "Failed Jobs: " + ", ".join(failed_jobs)
            run_info.append(run_message_line)
            counter += 1
        if len(run_info) == 0:
            alert_message += " Sorry we could not retrieving the run info"
        else:
            alert_message += "\n".join(run_info)
        with open(settings.MANUAL_RESTART_REPORT_PATH, "a+") as alert_file:
            alert_file.write(alert_message)
        single_operator_run.triggered_alert = True
        single_operator_run.save()


@shared_task
@memcache_lock("check_jobs_status")
def check_jobs_status():
    runs_queryset = Run.objects.filter(status__in=(RunStatus.RUNNING, RunStatus.READY), execution_id__isnull=False)

    limit = 800
    i = 0
    while True:
        runs = runs_queryset[i : i + limit]
        i += limit
        if not runs:
            return

        remote_statuses = check_statuses_on_ridgeback(list(runs.values_list("execution_id")))
        if not remote_statuses:
            continue

        for run in runs:
            logger.info(format_log("Checking status for run", obj=run))
            if str(run.execution_id) not in remote_statuses:
                logger.info(format_log("Requested job status from executor that was not returned", obj=run))
                continue

            status = remote_statuses[str(run.execution_id)]
            message = dict(details=status.get("message", {}))
            new_alert = message.get("details", {}).get("alerts")
            old_alert = run.message.get("details", {}).get("alerts")
            if old_alert != new_alert:
                logger.error(format_log("Hanging Job detected", obj=run))
                run.message = dict(details=status.get("message", {}))
                run.save(update_fields=("message",))
                # send_hanging_job_alert(str(run.id), new_alert[0]["message"])

            if status["started"] and not run.started:
                run.started = status["started"]
                run.save(update_fields=("started",))
            if status["submitted"] and not run.submitted:
                run.submitted = status["submitted"]
                run.save(update_fields=("submitted",))

            if status["commandlinetooljob_set"]:
                update_commandline_job_status(run, status["commandlinetooljob_set"])
            if status["status"] == "FAILED":
                logger.error(format_log("Job failed ", obj=run))
                message = dict(details=status.get("message"))
                run_log_location = status.get("message", {}).get("log")
                inputs_location = None
                if run_log_location:
                    run_log_filename = os.path.basename(run_log_location)
                    inputs_location = run_log_location.replace(run_log_filename, "input.json")
                fail_job.delay(str(run.id), message, run_log_location, inputs_location)
                continue
            if status["status"] == "COMPLETED":
                logger.info(format_log("Job completed", obj=run))
                run_log_location = status.get("message", {}).get("log")
                inputs_location = None
                if run_log_location:
                    run_log_filename = os.path.basename(run_log_location)
                    inputs_location = run_log_location.replace(run_log_filename, "input.json")
                complete_job.delay(str(run.id), status["outputs"], run_log_location, inputs_location)
                continue
            if status["status"] == "CREATED":
                logger.info(format_log("Job created", obj=run))
                continue
            if status["status"] == "PENDING":
                logger.info(format_log("Job pending", obj=run))
                continue
            if status["status"] == "RUNNING":
                logger.info(format_log("Job running", obj=run))
                running_job.delay(str(run.id))
                continue
            if status["status"] == "TERMINATED":
                logger.info(format_log("Job terminated", obj=run))
                run_log_location = status.get("message", {}).get("log")
                inputs_location = None
                if run_log_location:
                    run_log_filename = os.path.basename(run_log_location)
                    inputs_location = run_log_location.replace(run_log_filename, "input.json")
                terminate_job.delay(str(run.id), run_log_location, inputs_location)
            else:
                logger.info("Run lock not acquired for run: %s" % str(run.id))


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


@shared_task
@memcache_lock("add_cache_lock")
def add_pipeline_to_cache(github, version):
    if not GithubCache.get(github, version):
        GithubCache.add(github, version)
