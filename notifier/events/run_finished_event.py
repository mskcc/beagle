import json
from django.conf import settings
from notifier.event_handler.event import Event


class RunFinishedEvent(Event):
    def __init__(
        self,
        job_notifier,
        request_id,
        run_id,
        pipeline,
        pipeline_version,
        pipeline_link,
        output_directory,
        run_status,
        tags,
        running,
        completed,
        failed,
        total,
        operator_run_id,
        lsf_log_location,
        input_json_location,
        job_group_id,
    ):
        self.job_notifier = job_notifier
        self.request_id = request_id
        self.pipeline = pipeline
        self.pipeline_version = pipeline_version
        self.pipeline_link = pipeline_link
        self.output_directory = output_directory
        self.run_id = run_id
        self.run_status = run_status
        self.tags = tags
        self.running = running
        self.completed = completed
        self.failed = failed
        self.total = total
        self.operator_run_id = operator_run_id
        self.lsf_log_location = lsf_log_location
        self.input_json_location = input_json_location
        self.job_group_id = job_group_id

    @classmethod
    def get_type(cls):
        return "RunFinishedEvent"

    @classmethod
    def get_method(cls):
        return "process_run_completed"

    def __str__(self):
        RUN_TEMPLATE = """

        Run Id: {run_id}
        Pipeline: {pipeline_name}
        Pipeline Link: {pipeline_link}
        Output Directory: {output_directory}
        {tags}
        Status: {status}
        Link: {link}
        LSF Log Location: {lsf_log_location}
        inputs.json Location: {inputs_json_location}
        Datadog link: {datadog_link}
        
        _____________________________________________
        
        {run_status}
        
        Running: {running}
        Completed: {completed}
        Failed: {failed}
        
        TOTAL: {total}
        \n
        {rerun_info}
        """
        link = "%s%s%s\n" % (settings.BEAGLE_URL, "/v0/run/api/", self.run_id)
        if self.operator_run_id:
            status = "OperatorRun {operator_run} status".format(operator_run=self.operator_run_id)
        else:
            status = "Run status"
        tags = ""
        run_ids = None
        for k, v in self.tags.items():
            tags += f"{k}: {json.dumps(v) if isinstance(v, list) or isinstance(v, dict) else str(v)}\n"
            if k == "argos_run_ids":
                run_ids = v

        rerun_json = {}
        datadog_url = settings.DATADOG_RUN_ERROR_URL + self.run_id
        datadog_link = "[Voyager Run Error View ({})|{}]".format(self.run_id, datadog_url)
        rerun_json["pipelines"] = [self.pipeline]
        rerun_json["pipeline_versions"] = [self.pipeline_version]
        rerun_json["job_group_id"] = self.job_group_id
        if run_ids:
            rerun_json["run_ids"] = run_ids
        else:
            rerun_json["request_ids"] = self.request_id

        if self.run_status == "FAILED":
            rerun_str = f"""
            API Body for re-run:
            
            {json.dumps(rerun_json)}
            """
        else:
            rerun_str = ""

        return RUN_TEMPLATE.format(
            run_id=self.run_id,
            pipeline_name=self.pipeline,
            pipeline_link=self.pipeline_link,
            status=self.run_status,
            link=link,
            datadog_link=datadog_link,
            running=str(self.running),
            completed=str(self.completed),
            failed=str(self.failed),
            total=str(self.total),
            tags=tags,
            run_status=status,
            output_directory=self.output_directory,
            lsf_log_location=self.lsf_log_location,
            inputs_json_location=self.input_json_location,
            rerun_info=rerun_str,
        )
