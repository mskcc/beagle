import os
import logging
from datetime import datetime
from django.conf import settings
from beagle import __version__
from datetime import datetime
from file_system.models import File, FileGroup, FileType, FileMetadata
from runner.operator.operator import Operator
from runner.models import Run, Pipeline
from runner.run.objects.run_creator_object import RunCreator
from runner.run.processors.file_processor import FileProcessor
from notifier.events import OperatorRequestEvent
from notifier.models import JobGroup
from notifier.tasks import send_notification

LOGGER = logging.getLogger(__name__)

ARGOS_NAME = "argos"
ARGOS_VERSION = "1.1.2"
ONCOKB_FG_SLUG = "oncokb-file-group"


class ArgosReportOperator(Operator):
    def get_jobs(self):
        LOGGER.info("[%s] Running ArgosReportOperator", self.job_group_notifier_id)
        self.annotations_path = "juno:///juno/work/ci/resources/genomic_resources/annotations/oncokb"

        hf_run_id = self.run_ids[0]  # only one run in list
        hf_run = Run.objects.get(id=hf_run_id)
        project_prefix = hf_run.tags["project_prefix"]

        inputs = self.gen_inputs(hf_run)
        app = self.get_pipeline_id()
        jobs = list()
        pipeline = Pipeline.objects.get(id=app)
        output_directory = self.gen_output_dir(pipeline, project_prefix)

        for i, input in enumerate(inputs):
            name = "ARGOS Report: %s" % project_prefix
            tags = {"name": name, "project_prefix": project_prefix, "app": app}
            jobs.append(RunCreator(app=app, inputs=input, name=name, tags=tags, output_directory=output_directory))

        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")
        beagle_version = __version__

        self.send_message(
            """
            Writing HTML report files to {file_path}.

            Run Date: {run_date}
            Beagle Version: {beagle_version}
            """.format(
                file_path=output_directory, run_date=run_date, beagle_version=beagle_version
            )
        )

        return jobs

    def gen_output_dir(self, pipeline, project_prefix):
        jg = JobGroup.objects.get(id=self.job_group_id)
        jg_created_date = jg.created_date.strftime("%Y%m%d_%H_%M_%f")
        output_directory = os.path.join(
            pipeline.output_directory, ARGOS_NAME, project_prefix, ARGOS_VERSION, jg_created_date, "report"
        )
        return output_directory

    def gen_inputs(self, hf_run):
        request_id = hf_run.tags["project_prefix"]
        samples = hf_run.samples.all()
        ports = hf_run.port_set.all()
        analysis_dir_path = dict()
        portal_dir_path = dict()
        ci_tags = self.get_ci_tags(samples)

        for port in ports:
            if port.name == "analysis_dir":
                analysis_dir_path = {
                    "class": "Directory",
                    "path": FileProcessor.parse_path_from_uri(port.value["location"]),
                }
            if port.name == "portal_dir":
                portal_dir_path = {
                    "class": "Directory",
                    "path": FileProcessor.parse_path_from_uri(port.value["location"]),
                }

        inputs = list()
        for ci_tag in ci_tags:
            input = dict()
            input["request_id"] = request_id
            input["sample_id"] = ci_tag
            input["portal_dir"] = portal_dir_path
            input["analysis_dir"] = analysis_dir_path
            input["oncokb_file"] = self.get_oncokb_file(self.annotations_path)
            inputs.append(input)
        return inputs

    def get_ci_tags(self, samples):
        ci_tags = set()
        # get ci_tag from file metadata
        for sample in samples:
            if sample.sample_type:
                if "normal" not in sample.sample_type.lower():
                    sample_id = sample.sample_id
                    query = {f"metadata__{settings.SAMPLE_ID_METADATA_KEY}": sample_id}
                    files = FileMetadata.objects.filter(**query)
                    for f in files:
                        ci_tags.add(f.metadata["ciTag"])
        return ci_tags

    def get_oncokb_file(self, annotations_path):
        oncokb_dir = FileProcessor.parse_path_from_uri(annotations_path)
        oncokb_files = os.listdir(oncokb_dir)
        latest_file = sorted([f for f in oncokb_files if os.path.isfile(oncokb_dir + os.sep + f)])[-1]
        oncokb_file_path = os.path.join(oncokb_dir, latest_file)
        oncokb_file_registered = self._register_oncokb_file(oncokb_file_path)

        oncokb_entry = {
            "class": "File",
            "path": oncokb_file_path,
        }

        return oncokb_entry

    def _register_oncokb_file(self, oncokb_fp):
        file_group = FileGroup.objects.get(slug=ONCOKB_FG_SLUG)
        file_type = FileType.objects.filter(name="rds").first()
        return self._create_file_obj(path=oncokb_fp, file_group=file_group, file_type=file_type)

    def send_message(self, msg):
        event = OperatorRequestEvent(self.job_group_notifier_id, msg)
        e = event.to_dict()
        send_notification.delay(e)

    def _create_file_obj(self, path, file_group, file_type):
        """
        Tries to create a File from path provided
        Returns True if file is created; False if file at path exists
        """
        file_exists = File.objects.filter(path=path).exists()
        if not file_exists:
            try:
                f = File.objects.create(
                    file_name=os.path.basename(path), path=path, file_group=file_group, file_type=file_type
                )
                f.save()
                LOGGER.info("Adding OncoKB RDS file to database: %s" % path)
                return True
            except Exception as e:
                LOGGER.error("Failed to create file %s. Error %s" % (path, str(e)))
                raise Exception("Failed to create file %s. Error %s" % (path, str(e)))
        else:
            return False
