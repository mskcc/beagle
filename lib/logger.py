def format_log(message, obj=None, obj_id=None, operator_run_id=None, job_group_id=None, request_id=None):
    if hasattr(obj, "id"):
        obj_id = obj.id
    if hasattr(obj, "operator_obj_id"):
        operator_run_id = obj.operator_run_id
    if hasattr(obj, "job_group_id"):
        job_group_id = obj.job_group_id
    execution_id = None
    if hasattr(obj, "execution_id"):
        execution_id = obj.execution_id

    if not request_id:
        request_id = get_tag_from_obj(obj, "request_id")

    return "[%s] [%s] [%s] [%s] [%s] [%s] %s" % (str(obj_id),
                                                 str(operator_run_id),
                                                 str(job_group_id),
                                                 str(execution_id), request_id,
                                                 get_tag_from_obj(obj, "sample_id"), message)

def get_tag_from_obj(obj, tag):
    if obj and hasattr(obj, "tags"):
        if tag in obj.tags:
            return obj.tags[tag]
    return "None"


