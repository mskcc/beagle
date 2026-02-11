import os
import json
import uuid
import logging
from pathlib import Path
from jinja2 import Template
from beagle import settings
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from file_system.models import File, FileGroup, FileType
from file_system.helper.access_helper import CmoDMPManifest
from runner.operator.access import get_request_id

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
    """

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        # get request id
        self.request_id = get_request_id(self.run_ids, self.request_id)
        # make manifest and get path
        manifest_path = self.generate_manifest()
        # create job input json with manifest path
        job = self.construct_sample_input(manifest_path)
        # submit file to RunCreator
        # uses a cwl that returns the created manifest csv: https://github.com/msk-access/cwl_pass_through
        return [
            RunCreator(
                **{
                    "name": "Manifest Operator %s" % (self.request_id),
                    "app": self.get_pipeline_id(),
                    "inputs": job,
                    "tags": {
                        settings.REQUEST_ID_METADATA_KEY: self.request_id,
                    },
                }
            )
        ]

    def generate_manifest(self):
        """
        creates manifest csv, write contents to file
        :return: manifest csv path
        """
        # Construct manifest via requestid
        manifest_csv = CmoDMPManifest([self.request_id]).csv.content.decode()
        output_directory = self.write_to_file("manifest.csv", manifest_csv)
        return output_directory

    def write_to_file(self, fname, s):
        """
        Writes manifest csv to temporary location, registers it as tmp file
        :return: manifest csv path
        """
        # output path
        tmpdir = os.path.join(settings.BEAGLE_SHARED_TMPDIR, str(uuid.uuid4()))
        Path(tmpdir).mkdir(parents=True, exist_ok=True)
        output = os.path.join(tmpdir, fname)
        # write csv to tmp file group
        with open(output, mode="w", encoding="utf-8", newline="") as file:
            file.write(s)
        # register output as tmp file
        self.register_temp_file(output)
        # return with iris formatting
        return {"class": "File", "location": "iris://" + output}

    def construct_sample_input(self, manifest_dir):
        with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
            template = Template(file.read())
        job = {}
        job["manifest_data"] = manifest_dir

        input_file = template.render(**job)
        input_file = input_file.replace("'", '"')
        sample_input = json.loads(input_file)
        return sample_input

    @staticmethod
    def register_temp_file(output):
        os.chmod(output, 0o777)
        fname = os.path.basename(output)
        temp_file_group = FileGroup.objects.get(slug="temp")
        file_type = FileType.objects.get(name="unknown")
        f = File(file_name=fname, path=output, file_type=file_type, file_group=temp_file_group)
        f.save()
