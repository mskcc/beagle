from runner.models import Run, RunStatus


def get_request_id_runs(request_id):
    """
    Get the latest completed runs for the given request ID

    :param request_id: str - IGO request ID
    :return: List[str] - List of most recent runs from given request ID
    """
    group_id = Run.objects.filter(
        tags__requestId=request_id,
        app__name='access legacy',
        status=RunStatus.COMPLETED
    ).order_by('-finished_date').first().job_group

    request_id_runs = Run.objects.filter(
        job_group=group_id,
        status=RunStatus.COMPLETED
    )
    return request_id_runs
