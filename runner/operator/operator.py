import logging
from ddtrace import tracer
from django.conf import settings
from file_system.repository.file_repository import FileRepository
from runner.serializers import OperatorErrorSerializer
from beagle_etl.models import Operator as OperatorModel
from runner.operator.operator_logger import OperatorLogger
from runner.run.objects.run_creator_object import RunCreator


class Operator(object):
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        model,
        job_group_id=None,
        job_group_notifier_id=None,
        request_id=None,
        run_ids=[],
        pipeline=None,
        pairing=None,
        output_directory_prefix=None,
        file_group=None,
        **kwargs
    ):
        if not isinstance(model, OperatorModel):
            raise Exception("Must pass an instance of beagle_etl.models.Operator")

        self.model = model
        self.request_id = request_id
        self.job_group_id = job_group_id
        self.job_group_notifier_id = job_group_notifier_id
        self.run_ids = run_ids
        self.file_group = file_group
        if not self.file_group:
            self.file_group = settings.IMPORT_FILE_GROUP
        self.files = FileRepository.filter(file_group=self.file_group).all()
        self.pairing = pairing
        # {"pairs": [{"tumor": "tumorSampleName", "normal": "normalSampleName"}]}
        self.output_directory_prefix = output_directory_prefix
        self._jobs = []
        self._pipeline = pipeline
        self.logger = OperatorLogger()

    def get_pipeline_id(self):
        if self._pipeline:
            return self._pipeline
        return str(self.model.pipeline_set.filter(default=True).first().pk)

    def get_jobs(self):
        """

        :return: ([RunCreator])
        """
        return self._jobs

    def get_output_metadata(self):
        """
        Override this method to set proper metadata to output files
        :return: dict
        """
        return {}

    def failed_to_create_job(self, error):
        operator_error = OperatorErrorSerializer(
            data={"operator_name": self.model.slug, "request_id": self.request_id, "error": error}
        )
        current_span = tracer.current_span()
        if operator_error.is_valid():
            cmo_request_id = self.request_id
            current_span.set_tag("request.id", cmo_request_id)
            operator_error.save()
            self.logger.info(
                "Operator: %s failed to create a job for request_id: %s with error: %s"
                % (self.model.slug, self.request_id, str(error))
            )
        else:
            self.logger.error("Invalid Operator: %s error" % self.model.slug)

    def on_job_fail(self, run):
        pass

    def links_to_files(self):
        """
        Override this method to put the list of operator generated files into the ticket description
        :return: list[string]
        """
        return {}
