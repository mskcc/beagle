from runner.tasks import create_jobs_from_request
from runner.models import OperatorRun, RunStatus
from study.models import JobGroupWatcher, JobGroupWatcherStatus


def kick_off_postprocessing(job_group_watcher):
    for operator in job_group_watcher.config.post_processors:
        create_jobs_from_request.delay(
            job_group_watcher.study.requests[0], operator.id, str(job_group_watcher.job_group.id)
        )
        job_group_watcher.status = JobGroupWatcherStatus.COMPLETED
        job_group_watcher.save()


def check_job_group_watcher():
    watchers = JobGroupWatcher.objects.filter(status=JobGroupWatcherStatus.WAITING)
    for watcher in watchers:
        operator_runs = OperatorRun.objects.filter(job_group=watcher.job_group)
        waiting_operators = watcher.config.operators
        for operator_run in operator_runs:
            if operator_run.operator_finished:
                waiting_operators.remove(operator_run.operator)
        if waiting_operators.count() == 0:
            watcher.complete()
            kick_off_postprocessing(watcher)
