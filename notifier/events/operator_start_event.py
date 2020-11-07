from notifier.event_handler.event import Event


class OperatorStartEvent(Event):

    def __init__(self, job_notifier, job_group, request_id, sample_list_completed, recipe, data_analyst_name,
                 data_analyst_email, investigator_name, investigator_email, lab_head_name, lab_head_email, pi_email,
                 project_manager_name, qc_access_emails, number_of_tumors, number_of_normals):
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
        Recipe: {recipe}
        Data Analyst Name: {data_analyst_name}
        Data Analyst e-mail: {data_analyst_email}
        Investigator Name: {investigator_name}
        Investigator e-mail: {investigator_email}
        Lab Head Name: {lab_head_name}
        Lab Head e-mail: {lab_head_email}
        PI E-mail: {pi_email}
        Project Manager Name: {project_manager_name}
        QC E-mails: {qc_access_emails}

        Number of tumor samples: {number_of_tumors}
        Number of normal samples: {number_of_normals}
        Job Group ID: {job_group}
        
        Pipelines:
        | PIPELINE_NAME | PIPELINE_VERSION | PIPELINE_LINK |
        """
        return OPERATOR_START_TEMPLATE.format(request_id=self.request_id,
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
                                              job_group=self.job_group
                                              )
