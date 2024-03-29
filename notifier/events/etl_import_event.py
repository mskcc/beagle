from django.conf import settings
from notifier.event_handler.event import Event


class ETLImportEvent(Event):
    def __init__(
        self,
        job_notifier,
        job_group,
        request_id,
        sample_list_completed,
        sample_list_fail,
        recipe,
        data_analyst_email,
        data_analyst_name,
        investigator_email,
        investigator_name,
        lab_head_email,
        lab_head_name,
        pi_email,
        project_manager_name,
        qc_access_emails,
        number_of_tumors,
        number_of_normals,
        number_of_pool_normals,
        data_access_emails,
        other_contact_emails,
    ):
        self.job_notifier = job_notifier
        self.job_group = job_group
        self.request_id = request_id
        self.sample_list_completed = sample_list_completed
        self.sample_list_fail = sample_list_fail
        self.recipe = recipe
        self.data_analyst_email = data_analyst_email
        self.data_analyst_name = data_analyst_name
        self.investigator_email = investigator_email
        self.investigator_name = investigator_name
        self.lab_head_email = lab_head_email
        self.lab_head_name = lab_head_name
        self.pi_email = pi_email
        self.project_manager_name = project_manager_name
        self.qc_access_emails = qc_access_emails
        self.number_of_tumors = number_of_tumors
        self.number_of_normals = number_of_normals
        self.number_of_pool_normals = number_of_pool_normals
        self.data_access_emails = data_access_emails
        self.other_contact_emails = other_contact_emails

    @classmethod
    def get_type(cls):
        return "ETLImportEvent"

    @classmethod
    def get_method(cls):
        return "process_import_event"

    def __str__(self):
        ETL_IMPORT_MESSAGE_TEMPLATE = """
        Request imported: {request_id}
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

        {cnt_samples_completed} samples successfully imported
        {cnt_samples_fail} samples failed

        Number of tumor samples: {number_of_tumors}
        Number of normal samples: {number_of_normals}
        Number of pooled normals: {number_of_pool_normals}
        Job Group ID: {job_group}
        """

        return ETL_IMPORT_MESSAGE_TEMPLATE.format(
            request_id=self.request_id,
            cnt_samples=self.sample_list_completed + self.sample_list_fail,
            cnt_samples_completed=self.sample_list_completed,
            cnt_samples_fail=self.sample_list_fail,
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
            number_of_pool_normals=self.number_of_pool_normals,
            job_group=self.job_group,
            data_access_emails=self.data_access_emails,
            other_contact_emails=self.other_contact_emails,
        )
