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


class AccessV2NucleoQcOperator(Operator):
    """
    Operator for the ACCESS QC workflow:

    https://github.com/msk-access/access_qc_generation/blob/master/access_qc.cwl

    This Operator will search for Nucleo Bam files based on an IGO Request ID
    """

    def get_jobs(self):

        sample_inputs = self.get_nucleo_outputs()

        return [
            RunCreator(
                **{
                    "name": "Access V2 Nucleo QC: %s, %i of %i" % (self.request_id, i + 1, len(sample_inputs)),
                    "app": self.get_pipeline_id(),
                    "inputs": job,
                    "output_metadata": output_metadata,
                    "tags": {settings.REQUEST_ID_METADATA_KEY: self.request_id, "cmoSampleId": job["sample_name"]},
                }
            )
            for i, (job, output_metadata) in enumerate(sample_inputs)
        ]

    def get_nucleo_outputs(self):
        if not self.request_id:
            most_recent_runs_for_request = Run.objects.filter(pk__in=self.run_ids)
            self.request_id = most_recent_runs_for_request[0].tags["igoRequestId"]
        else:
            # Use most recent set of runs that completed successfully
            most_recent_runs_for_request = (
                Run.objects.filter(
                    app__name="access v2 nucleo",
                    tags__igoRequestId=self.request_id,
                    status=RunStatus.COMPLETED,
                    operator_run__status=RunStatus.COMPLETED,
                )
                .order_by("-created_date")
                .first()
                .operator_run.runs.all()
                .filter(status=RunStatus.COMPLETED)
            )
            if not len(most_recent_runs_for_request):
                raise Exception("No matching Access V2 Nucleo runs found for request {}".format(self.request_id))

        inputs = []
        for r in most_recent_runs_for_request:
            inp = self.construct_sample_inputs(r)
            output_metadata = r.output_metadata
            inputs.append((inp, output_metadata))
        return inputs

    def parse_nucleo_output_ports(self, run, port_name):
        bam_bai = Port.objects.get(name=port_name, run=run.pk)
        if not len(bam_bai.files.all()) in [1, 2]:
            raise Exception("Port {} for run {} should have just 1 bam or 1 (bam/bai) pair".format(port_name, run.id))

        bam = [b for b in bam_bai.files.all() if b.file_name.endswith(".bam")][0]
        bai = [b for b in bam_bai.files.all() if b.file_name.endswith(".bai")]
        bam = self.create_cwl_file_object(bam.path)
        if len(bai):
            bam["secondaryFiles"] = [self.create_cwl_file_object(bai[0].path)]

        return bam

    def construct_sample_inputs(self, run):
        with open(os.path.join(WORKDIR, "input_template.json.jinja2")) as file:
            template = Template(file.read())

        nucleo_output_port_names = [
            "uncollapsed_bam",
            "fgbio_group_reads_by_umi_bam",
            "fgbio_collapsed_bam",
            "fgbio_filter_consensus_reads_duplex_bam",
            "fgbio_postprocessing_simplex_bam",
        ]
        qc_input_port_names = [
            "uncollapsed_bam_base_recal",
            "group_reads_by_umi_bam",
            "collapsed_bam",
            "duplex_bam",
            "simplex_bam",
        ]
        bams = {}
        for o, i in zip(nucleo_output_port_names, qc_input_port_names):
            # We are running a multi-sample workflow on just one sample,
            # so we create single-element lists here
            bam = [self.parse_nucleo_output_ports(run, o)]
            bams[i] = json.dumps(bam)

        sample_sex = run.output_metadata["sex"]
        sample_name = run.output_metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY]
        sample_group = "-".join(sample_name.split("-")[0:2])
        samples_json_content = self.create_sample_json(run)

        input_file = template.render(
            sample_sex=json.dumps([sample_sex]),
            sample_name=json.dumps([sample_name]),
            sample_group=json.dumps([sample_group]),
            samples_json_content=json.dumps(samples_json_content),
            **bams,
        )
        sample_input = json.loads(input_file)
        return sample_input

    @staticmethod
    def create_cwl_file_object(file_path):
        return {"class": "File", "location": "iris://" + file_path}

    def create_sample_json(self, run):
        j = run.output_metadata
        # todo: cmoSampleName in output_metadata for Nucleo appears to be the igo ID?
        j[settings.CMO_SAMPLE_TAG_METADATA_KEY] = run.output_metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY]

        for f in meta_fields:
            # Use None for missing fields
            if not f in j:
                j[f] = None
        for f in j:
            # MultiQC cannot handle cells with ","
            if type(j[f]) is str and "," in j[f]:
                j[f] = j[f].replace(",", ";")
        # Use some double quotes to make JSON compatible
        j["qcReports"] = "na"
        out = json.dumps([j])

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
