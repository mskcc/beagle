import notifier.tasks as notifier
from django.db import models
from notifier.event_handler.jira_event_handler.jira_event_handler import JiraEventHandler
from file_system.repository.file_repository import FileRepository
from beagle_etl.models import Operator
from runner.operator.operator_factory import OperatorFactory
from runner.tasks import create_jobs_from_request

import datetime


class RequestObj:
    def __init__(self, req_id, job_group_id, pipeline_name):
        self.data = dict()
        self.set_request(req_id)
        self.set_job_group(job_group_id)
        self.set_pipeline_name(pipeline_name)

    def set_request(self, req_id):
        self.data['request_ids'] = req_id

    def set_job_group(self, job_group):
        self.data['job_group_id'] = job_group

    def set_pipeline_name(self, pipeline_name):
        self.data['pipeline_name'] = pipeline_name


def run_request(req_id, operator_class_name):
    approx_create_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    files = FileRepository.filter(metadata={'requestId': req_id, 'igocomplete': True})
    # create summary and description
    summary = req_id + " [%s]" % approx_create_time
    description = create_description(files)
    # place values into jira ticket
    job_group = JobGroup()
    job_group.save()
    notifier.notifier_start(job_group, req_id) 
    jira_eh = JiraEventHandler()
    jira_eh.client.update_ticket_summary(job_group.jira_id, summary)
    jira_eh.client.update_ticket_description(job_group.jira_id, description)
    # submit job through post query
    operator_model = Operator.objects.filter(class_name=operator_class_name)[0]
    op_id = operator_model.id
    create_jobs_from_request(req_id, op_id, str(job_group.id))

def create_description(files):
    data = files.first().metadata
    request_id = data['requestId']
    recipe = data['recipe']
    a_name =  data['dataAnalystName']
    a_email = data['dataAnalystEmail']
    i_name = data['investigatorName']
    i_email = data['investigatorEmail']
    l_name = data['labHeadName']
    l_email = data['labHeadEmail']
    p_email = data['piEmail']
    pm_name = data['projectManagerName']
    num_samples = files.order_by().values('metadata__cmoSampleName').annotate(n=models.Count("pk"))
    # maybe a bug? can't re-filter files var, returns empty queryset, so re-doing FileRepository filter
    # TODO: investigate this
    num_tumors = len(FileRepository.filter(queryset=files,metadata={'tumorOrNormal': 'Tumor'}).order_by().values('metadata__cmoSampleName').annotate(n=models.Count("pk")))
    num_normals = len(FileRepository.filter(queryset=files,metadata={'tumorOrNormal': 'Normal'}).order_by().values('metadata__cmoSampleName').annotate(n=models.Count("pk")))
    description = """
        Request ID: {request_id}
        Number of samples: {cnt_samples}
        Recipe: {recipe}
        Data Analyst Name: {data_analyst_name}
        Data Analyst e-mail: {data_analyst_email}
        Investigator Name: {investigator_name}
        Investigator e-mail: {investigator_email}
        Lab Head Name: {lab_head_name}
        Lab Head e-mail: {lab_head_email}
        PI e-email: {pi_email}
        Project Manager Name: {project_manager_name}
        
        Number of tumor samples: {number_of_tumors}
        Number of normal samples: {number_of_normals}
        """
    return description.format(request_id=request_id,
                            cnt_samples = len(num_samples),
                            recipe = recipe,
                            data_analyst_name = a_name,
                            data_analyst_email = a_email,
                            investigator_name = i_name,
                            investigator_email = i_email,
                            lab_head_name = l_name,
                            lab_head_email = l_email,
                            pi_email = p_email,
                            project_manager_name = pm_name,
                            number_of_tumors = num_tumors,
                            number_of_normals = num_normals
                            )

