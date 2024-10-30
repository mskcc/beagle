import os
from django.conf import settings
from notifier.event_handler.event import Event
from notifier.models import JobGroupNotifier


class OperatorStartEvent(Event):
    def __init__(
        self,
        job_notifier,
        job_group,
        request_id,
        sample_list_completed,
        recipe,
        data_analyst_name,
        data_analyst_email,
        investigator_name,
        investigator_email,
        lab_head_name,
        lab_head_email,
        pi_email,
        project_manager_name,
        qc_access_emails,
        number_of_tumors,
        number_of_normals,
        data_access_emails,
        other_contact_emails,
        links={},
    ):
        self.job_notifier = job_notifier
        self.job_group = job_group
        self.request_id = request_id
        self.sample_list_completed = sample_list_completed
        self.recipe = recipe
        self.data_analyst_name = data_analyst_name
        self.data_analyst_email = data_analyst_email
        self.investigator_name = investigator_name
        self.investigator_email = investigator_email
        self.lab_head_name = lab_head_name
        self.lab_head_email = lab_head_email
        self.pi_email = pi_email
        self.project_manager_name = project_manager_name
        self.number_of_tumors = number_of_tumors
        self.number_of_normals = number_of_normals
        self.qc_access_emails = qc_access_emails
        self.data_access_emails = data_access_emails
        self.other_contact_emails = other_contact_emails
        self.links = links

    @classmethod
    def get_type(cls):
        return "OperatorStartEvent"

    @classmethod
    def get_method(cls):
        return "process_operator_start_event"

    def __str__(self):
        OPERATOR_START_TEMPLATE = """
        Request ID: {request_id}
        Number of samples: {cnt_samples}
        Gene Panel: {recipe}
        Data Analyst Name: {data_analyst_name}
        Data Analyst e-mail: {data_analyst_email}
        Investigator Name: {investigator_name}
        Investigator e-mail: {investigator_email}
        Lab Head Name: {lab_head_name}
        Lab Head e-mail: {lab_head_email}
        PI E-mail: {pi_email}
        Project Manager Name: {project_manager_name}
        QC E-mails: {qc_access_emails}
        Data Access Emails: {data_access_emails}
        Other Contact Emails: {other_contact_emails}

        Number of tumor samples: {number_of_tumors}
        Number of normal samples: {number_of_normals}
        Job Group ID: {job_group}
        Datadog link: {datadog_link}
        JIRA local attachment path: `{jira_output_path}`
        {links}

        Pipelines:
        | PIPELINE_NAME | PIPELINE_VERSION | PIPELINE_LINK |
        """

        datadog_url = settings.DATADOG_JOB_ERROR_URL + self.job_group
        datadog_link = "[Voyager Job Error View ({})|{}]".format(self.job_group, datadog_url)
        job_group_notifier = JobGroupNotifier.objects.get(id=self.job_notifier)
        jira_output_path = os.path.join(
            settings.NOTIFIER_LOCAL_ATTACHMENTS_DIR, job_group_notifier.request_id, job_group_notifier.jira_id
        )
        LINKS = ""
        if self.links:
            LINKS = """Links:
            """
            for name, link in self.links.items():
                LINKS += f"[{name}]({link})\n"

        return OPERATOR_START_TEMPLATE.format(
            request_id=self.request_id,
            cnt_samples=self.sample_list_completed,
            recipe=self.recipe,
            data_analyst_name=self.data_analyst_name,
            data_analyst_email=self.data_analyst_email,
            investigator_name=self.investigator_name,
            investigator_email=self.investigator_email,
            lab_head_name=self.lab_head_name,
            lab_head_email=self.lab_head_email,
            pi_email=self.pi_email,
            project_manager_name=self.project_manager_name,
            qc_access_emails=self.qc_access_emails,
            number_of_tumors=self.number_of_tumors,
            number_of_normals=self.number_of_normals,
            job_group=self.job_group,
            datadog_link=datadog_link,
            jira_output_path=jira_output_path,
            data_access_emails=self.data_access_emails,
            other_contact_emails=self.other_contact_emails,
            links=LINKS,
        )
