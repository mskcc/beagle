import os
import json
import uuid
import logging
from pathlib import Path
from jinja2 import Template
from beagle import settings
from runner.operator.operator import Operator
from runner.models import RunStatus, Port, Run
from runner.run.objects.run_creator_object import RunCreator
from file_system.models import File, FileGroup, FileType
from file_system.repository import FileRepository
from runner.tasks import cmo_dmp_manifest
from runner.operator.access import get_request_id, get_request_id_runs, create_cwl_file_object
import csv
import datetime

logger = logging.getLogger(__name__)

WORKDIR = os.path.dirname(os.path.abspath(__file__))


meta_fields = [
    "igoId",
    settings.CMO_SAMPLE_TAG_METADATA_KEY,
    settings.CMO_SAMPLE_NAME_METADATA_KEY,
    settings.CMO_SAMPLE_CLASS_METADATA_KEY,
    settings.PATIENT_ID_METADATA_KEY,
    "investigatorSampleId",
    settings.ONCOTREE_METADATA_KEY,
    "tumorOrNormal",
    "tissueLocation",
    settings.SAMPLE_CLASS_METADATA_KEY,
    "sampleOrigin",
    "preservation",
    "collectionYear",
    "sex",
    "species",
    "tubeId",
    "cfDNA2dBarcode",
    "baitSet",
    "qcReports",
    "barcodeId",
    "barcodeIndex",
    settings.LIBRARY_ID_METADATA_KEY,
    "libraryVolume",
    "libraryConcentrationNgul",
    "dnaInputNg",
    "captureConcentrationNm",
    "captureInputNg",
    "captureName",
]


class AccessManifestOperator(Operator):
    """
    Operator to create a manifest report (merged dmp and fastq metadata) for a given access request.

    It doesn't use a cwl, but rather the internal cmo_dmp_manifest class,
    which generates the manifest using internal queries.
    """

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        self.request_id = get_request_id(self.run_ids, self.request_id)
        request_output_directory = self.get_request_output_directory()
        # The run really isn't "submitted", there are no job inputs since there is no cwl.
        # The run more or less documents that the operator ran from inside Voyager.
        job = self.construct_sample_input(request_output_directory)
        return [
            RunCreator(
                **{
                    "name": "Manifest Operator %s" % (self.request_id),
                    "app": self.get_pipeline_id(),
                    "inputs": job,
                    "tags": {
                        settings.REQUEST_ID_METADATA_KEY: self.request_id,
                    }
                    # ,"output_directory": request_output_directory,
                }
            )
        ]
    
    def construct_sample_input(self, manifest_dir):
        with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
            template = Template(file.read())
        job = {}
        job["manifest_data"] = manifest_dir

        input_file = template.render(**job)
        input_file = input_file.replace("'", '"')
        sample_input = json.loads(input_file)
        return sample_input

    def get_request_output_directory(self):
        """
        Create manifest report and write contents to file and return output directory of written file

        :return: a juno output directory specifying the manifests location
        """
        # Construct manifest via requestid
        manifest_csv = cmo_dmp_manifest([self.request_id]).csv.content.decode()
        output_directory = self.write_to_file("manifest.csv", manifest_csv)
        return output_directory
    
    def write_to_file(self, fname, s):
        """
        Writes file to temporary location, then registers it to the manifest file group
        Also uploads it to notifier if there is a job group id
        """
        # current_datetime = datetime.datetime.now()
        # current_datetime_string = current_datetime.strftime("%Y-%m-%d_%H-%M")
        # output = os.path.join(self.OUTPUT_DIR, self.request_id, current_datetime_string, fname)
        # Split the string into rows using "\r\n" as the delimiter
        rows = s.split("\r\n")
        # Split each row into columns using "," as the delimiter
        data = [row.split(",") for row in rows]
        # # make dir if doesn't exist
        # os.makedirs(os.path.dirname(output), exist_ok=True)
        tmpdir = os.path.join(settings.BEAGLE_SHARED_TMPDIR, str(uuid.uuid4()))
        Path(tmpdir).mkdir(parents=True, exist_ok=True)
        output = os.path.join(tmpdir, fname)
        # Create a new CSV file and write the data to it
        with open(output, "w+", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(data)
        os.chmod(output, 0o777)
        fname = os.path.basename(output)
        temp_file_group = FileGroup.objects.get(slug="temp")
        file_type = FileType.objects.get(name="unknown")

        f = File(file_name=fname, path=output, file_type=file_type, file_group=temp_file_group)
        f.save()
        # self.register_manifest_file(output)
        return {"class": "File", "location": "juno://" + output}

    def register_manifest_file(self, path):
        fname = os.path.basename(path)
        file_group = FileGroup.objects.get(slug="access_manifests")
        file_type = FileType.objects.get(name="csv")
        try:
            File.objects.get(path=path)
        except:
            print("Registering temp file %s" % path)
            f = File(file_name=fname, path=path, file_type=file_type, file_group=file_group)
            f.save()
