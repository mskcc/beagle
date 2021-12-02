def format_log(message, obj=None, obj_id=None, operator_run_id=None, job_group_id=None, request_id=None):
    if hasattr(obj, "id"):
        obj_id = obj.id
    if hasattr(obj, "operator_run_id"):
        operator_run_id = obj.operator_run_id
    if hasattr(obj, "job_group_id"):
        job_group_id = obj.job_group_id
    execution_id = None
    if hasattr(obj, "execution_id"):
        execution_id = obj.execution_id

    if not request_id:
        request_id = get_tag_from_obj(obj, "requestId") or get_tag_from_obj(obj, "request_id")
    sample_id = (
        get_tag_from_obj(obj, "sampleId")
        or get_tag_from_obj(obj, "sample_id")
        or get_tag_from_obj(obj, "cmoSampleId")
        or get_tag_from_obj(obj, "cmoSampleIds")
    )

    return "[%s] [%s] [%s] [%s] [%s] [%s] %s" % (
        str(obj_id),
        str(operator_run_id),
        str(job_group_id),
        str(execution_id),
        str(request_id),
        str(sample_id),
        message,
    )


def get_tag_from_obj(obj, tag):
    data = None
    if obj and hasattr(obj, "tags"):
        data = obj.tags
    elif obj and hasattr(obj, "args"):
        data = obj.args

    if data and tag in data:
        return data[tag]

    return None
