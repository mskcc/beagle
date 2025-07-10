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


class AccessV2NucleoQcAggOperator(Operator):
    """
    Operator for the ACCESS QC AGGREGATE workflow:

    https://github.com/msk-access/nucleo_qc/blob/develop/nucleo_aggregate_visualize.cwl

    This Operator will search for ACCESS QC files based on an IGO Request ID
    """

    def get_jobs(self):

        job, sample_list = self.get_qc_outputs()

        return [
            RunCreator(
                **{
                    "name": "Access V2 Nucleo QC Aggregate: %s" % (self.request_id),
                    "app": self.get_pipeline_id(),
                    "inputs": job,
                    "tags": {settings.REQUEST_ID_METADATA_KEY: self.request_id, "cmoSampleIds": sample_list},
                }
            )
        ]

    def get_qc_outputs(self):
        # was the pipeline triggered from a chaining operator (runs) or executed with the api via the request id
        if not self.request_id:
            most_recent_runs_for_request = Run.objects.filter(pk__in=self.run_ids)
            self.request_id = most_recent_runs_for_request[0].tags["igoRequestId"]
        else:
            # Use most recent set of runs that completed successfully
            most_recent_runs_for_request = (
                Run.objects.filter(
                    app__name="access v2 nucleo qc",
                    tags__igoRequestId=self.request_id,
                    status=RunStatus.COMPLETED,
                    operator_run__status=RunStatus.COMPLETED,
                )
                .order_by("-created_date")
                .first()
                .operator_run.runs.all()
            )
            if not len(most_recent_runs_for_request):
                raise Exception("No matching Access V2 Nucleo QC runs found for request {}".format(self.request_id))

        input = self.construct_sample_input(most_recent_runs_for_request)
        sample_list = []
        for single_run in most_recent_runs_for_request:
            sample_list.append(single_run.output_metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY])
        return input, sample_list

    def process_listing(self, listing, name):
        for directory in listing:
            if directory["basename"] == name:
                if "listing" in directory:
                    files_list = []
                    # Only include files part of the directory, cwl globs may add matplotlib hidden config files here
                    for single_file in directory["listing"]:
                        if directory["location"] in single_file["location"]:
                            files_list.append(single_file)
                    directory["listing"] = files_list
                return directory
            if "listing" in directory:
                item = self.process_listing(directory["listing"], name)
                if item:
                    return item
        return None

    def get_directory_ports(self, run_list, port_input, directory_name):
        directory_list = []
        for single_run in run_list:
            port = Port.objects.get(name=port_input, run=single_run.pk)
            directory_port = self.process_listing(port.value["listing"], directory_name)
            if not directory_port:
                raise Exception("Run {} does not have the folder {}".format(single_run.pk, directory_name))
            if directory_port["listing"]:
                directory_folder = directory_port["listing"][0]
                if "listing" in directory_folder and not directory_folder["listing"]:
                    continue
                directory_list.append(directory_folder)
        return directory_list

    def get_file_ports(self, run_list, port_input, file_regex):
        file_list = []
        for single_run in run_list:
            port = Port.objects.get(name=port_input, run=single_run.pk)
            files = port.files.filter(path__regex=file_regex)
            if not files:
                raise Exception("Run {} does not have files matching {}".format(single_run.pk, file_regex))
            for single_file in files:
                file_list.append(self.create_cwl_file_object(single_file.path))
        return file_list

    def construct_sample_input(self, runs):
        with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
            template = Template(file.read())

        qc_output_port_directory_names = [
            "athena_coverage_report_dir",
            "collapsed_bam_duplex_metrics_dir",
            "collapsed_bam_stats_dir",
            "duplex_bam_sequence_qc_dir",
            "duplex_bam_stats_dir",
            "gatk_mean_quality_by_cycle_recal_dir",
            "simplex_bam_stats_dir",
            "uncollapsed_bam_stats_dir",
            "biometrics_extract_files_dir",
        ]

        job = {}
        # Most inputs are directories
        for single_directory in qc_output_port_directory_names:
            job[single_directory] = self.get_directory_ports(runs, "multiqc_output_dir", single_directory)

        # These inputs are files and so require different parsing
        job["duplex_extraction_files"] = self.find_biometric_files(job, "duplex.pickle")
        job["collapsed_extraction_files"] = self.find_biometric_files(job, "collapsed.pickle")

        samples_json_content = self.create_sample_json(runs)
        job["samples_json"] = samples_json_content

        input_file = template.render(**job)
        input_file = input_file.replace("'", '"')
        sample_input = json.loads(input_file)
        return sample_input

    @staticmethod
    def create_cwl_file_object(file_path):
        return {"class": "File", "location": "iris://" + file_path}

    @staticmethod
    def create_cwl_file_object_on_iris(file_path):
        """
        This creates a cwl file objects. Opting to use this method in find_biometric_files
        as it seems more consistent with what was in prior input.json(s) for this operator.
        """
        return {"class": "File", "location": file_path.replace("file://", "iris://", 1)}

    def find_biometric_files(self, job_dirs, ending):
        """
        We still need a special method for parsing biometric files

        job_dirs: the directories being used as inputs to the cwl, variable is previously generated by get_directory_ports
        ending: the ending of the files we want to parse from job_dirs
        outputs: cwl file objects
        """
        matching_files = []
        biometric_dir = job_dirs["biometrics_extract_files_dir"]
        for sample_dir in biometric_dir:
            sample_listing = sample_dir["listing"]
            for file in sample_listing:
                file_path = file["location"]
                if file_path.endswith(ending):
                    matching_files.append(self.create_cwl_file_object_on_iris(file_path))
        return matching_files

    def create_sample_json(self, runs):
        samples_json = []
        for single_run in runs:
            j = single_run.output_metadata
            # Use some double quotes to make JSON compatible
            j["qcReports"] = "na"
            samples_json.append(j)
        out = json.dumps(samples_json)

        tmpdir = os.path.join(settings.BEAGLE_SHARED_TMPDIR, str(uuid.uuid4()))
        Path(tmpdir).mkdir(parents=True, exist_ok=True)
        output = os.path.join(tmpdir, "samples_json.json")

        with open(output, "w+") as fh:
            fh.write(out)

        os.chmod(output, 0o777)

        fname = os.path.basename(output)
        temp_file_group = FileGroup.objects.get(slug="temp")
        file_type = FileType.objects.get(name="unknown")

        f = File(file_name=fname, path=output, file_type=file_type, file_group=temp_file_group)
        f.save()

        return self.create_cwl_file_object(f.path)
