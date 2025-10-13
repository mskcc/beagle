import os
import logging
from datetime import datetime
from django.conf import settings
from beagle import __version__
from datetime import datetime
from file_system.models import File, FileGroup, FileType, FileMetadata
from file_system.repository.file_repository import FileRepository
from runner.operator.operator import Operator
from runner.models import Run, Pipeline
from runner.run.objects.run_creator_object import RunCreator
from runner.run.processors.file_processor import FileProcessor
from notifier.events import OperatorRequestEvent
from notifier.models import JobGroup
from notifier.tasks import send_notification

LOGGER = logging.getLogger(__name__)

ARGOS_NAME = "argos"
ARGOS_VERSION = "1.8.0"
ONCOKB_FG_SLUG = "oncokb-file-group"


class ArgosReportOperator(Operator):
    def get_jobs(self):
        LOGGER.info("[%s] Running ArgosReportOperator", self.job_group_notifier_id)
        self.annotations_path = "iris:///data1/core001/work/ci/resources/genomic_resources/annotations/oncokb/"

        hf_run_id = self.run_ids[0]  # only one run in list
        hf_run = Run.objects.get(id=hf_run_id)
        project_prefix = hf_run.tags["project_prefix"]

        input = self.gen_inputs(hf_run)
        app = self.get_pipeline_id()
        jobs = list()
        pipeline = Pipeline.objects.get(id=app)
        output_directory = self.gen_output_dir(pipeline, project_prefix)

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
        ports = hf_run.port_set.all()
        analysis_dir_path = dict()
        portal_dir_path = dict()
        for port in ports:
            if port.name == "pairs":
                normal_list, tumor_list = self.get_sample_ids(port.value)
            if port.name == "analysis_dir":
                analysis_dir_path = {
                    "class": "Directory",
                    "location": FileProcessor.parse_path_from_uri(port.value["location"]),
                }
            if port.name == "portal_dir":
                portal_dir_path = {
                    "class": "Directory",
                    "location": FileProcessor.parse_path_from_uri(port.value["location"]),
                }
        input = dict()
        input["request_id"] = request_id
        input["tumor_ids"] = tumor_list
        input["normal_ids"] = normal_list
        input["portal_dir"] = portal_dir_path
        input["analysis_dir"] = analysis_dir_path
        input["oncokb_file"] = self.get_oncokb_file(self.annotations_path)
        return input

    def get_sample_ids(self, pair_dict):
        normal_list = []
        tumor_list = []
        for single_pair in pair_dict:
            normal_list.append(single_pair["normal_id"])
            tumor_list.append(single_pair["tumor_id"])
        return normal_list, tumor_list

    def get_oncokb_file(self, annotations_path):
        oncokb_dir = FileProcessor.parse_path_from_uri(annotations_path)
        oncokb_files = os.listdir(oncokb_dir)
        latest_file = sorted([f for f in oncokb_files if os.path.isfile(oncokb_dir + os.sep + f)])[-1]
        oncokb_file_path = os.path.join(oncokb_dir, latest_file)
        oncokb_file_registered = self._register_oncokb_file(oncokb_file_path)

        oncokb_entry = {
            "class": "File",
            "location": "iris://" + oncokb_file_path,
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
                metadata = FileMetadata(file=f, metadata={})
                metadata.save()
                LOGGER.info("Adding OncoKB RDS file to database: %s" % path)
                return True
            except Exception as e:
                LOGGER.error("Failed to create file %s. Error %s" % (path, str(e)))
                raise Exception("Failed to create file %s. Error %s" % (path, str(e)))
        else:
            return False
