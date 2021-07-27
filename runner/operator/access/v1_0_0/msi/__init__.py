"""""""""""""""""""""""""""""
" ACCESS-Pipeline MSI workflow operator
" http://www.github.com/mskcc/access-pipeline/workflows/msi.cwl
"""""""""""""""""""""""""""""

import os
import json
import logging
from jinja2 import Template

from file_system.models import File
from runner.operator.operator import Operator
from runner.operator.access import get_request_id, get_request_id_runs, create_cwl_file_object
from runner.models import Port, RunStatus
from runner.serializers import APIRunCreateSerializer


logger = logging.getLogger(__name__)

# Todo: needs to work for Nucleo bams as well
SAMPLE_ID_SEP = '_cl_aln'
TUMOR_SEARCH = '-L0'
NORMAL_SEARCH = '-N0'
STANDARD_BAM_SEARCH = '_cl_aln_srt_MD_IR_FX_BR.bam'
WORKDIR = os.path.dirname(os.path.abspath(__file__))

class AccessLegacyMSIOperator(Operator):
    """
    Operator for the ACCESS Legacy Microsatellite Instability workflow:

    http://www.github.com/mskcc/access-pipeline/workflows/subworkflows/msi.cwl

    This Operator will search for ACCESS Standard Bam files based on an IGO Request ID. It will
    also find the matched normals based on the patient ID.
    """

    @staticmethod
    def is_tumor(file):
        t_n_timepoint = file.file_name.split('-')[2]
        return not t_n_timepoint[0] == 'N'

    def get_sample_inputs(self):
        """
        Create all sample inputs for all runs triggered in this instance of the operator.

        :return: list of json_objects
        """
        run_ids = self.run_ids if self.run_ids else [r.id for r in get_request_id_runs(self.request_id)]

        # Get all standard bam ports for these runs
        standard_bam_ports = Port.objects.filter(
            name__in=['standard_bams', 'uncollapsed_bam'],
            run__id__in=run_ids,
            run__status=RunStatus.COMPLETED
        )

        standard_tumor_bams = [f for p in standard_bam_ports for f in p.files.all() if self.is_tumor(f)]

        sample_ids = []
        matched_normal_bams = []
        for standard_tumor_bam in standard_tumor_bams:
            tumor_sample_id = standard_tumor_bam.file_name.split('_cl_aln')[0]
            patient_id = '-'.join(tumor_sample_id.split('-')[0:2])

            # Find the matched Normal Standard bam (which could be associated with a different request_id)
            sample_search_start = patient_id + NORMAL_SEARCH
            matched_normal_bam = File.objects.filter(
                file_name__startswith=sample_search_start,
                file_name__endswith=STANDARD_BAM_SEARCH
            )
            if not len(matched_normal_bam) > 0:
                msg = 'No matching standard normal Bam found for patient {}'.format(patient_id)
                logger.warning(msg)
                continue

            matched_normal_bam = matched_normal_bam.order_by('-created_date').first()

            sample_ids.append(tumor_sample_id)
            matched_normal_bams.append(matched_normal_bam)

        sample_inputs = [self.construct_sample_inputs(
            sample_ids[i],
            standard_tumor_bams[i],
            matched_normal_bams[i]
        ) for i in range(0, len(sample_ids))]

        return sample_inputs

    def get_jobs(self):
        """
        Convert job inputs into serialized jobs

        :return: list[(serialized job info, Job)]
        """
        self.request_id = get_request_id(self.run_ids, self.request_id)
        inputs = self.get_sample_inputs()

        return [
            (
                APIRunCreateSerializer(
                    data={
                        'name': "ACCESS LEGACY MSI M1: %s, %i of %i" % (self.request_id, i + 1, len(inputs)),
                        'app': self.get_pipeline_id(),
                        'inputs': job,
                        'tags': {
                            'requestId': self.request_id,
                            'cmoSampleIds': job["sample_name"],
                            'patientId': '-'.join(job["sample_name"][0].split('-')[0:2])
                        }
                    }
                ),
                job
             )
            for i, job in enumerate(inputs)
        ]

    def construct_sample_inputs(self, sample_name, tumor_bam, matched_normal_bam):
        """
        Use sample metadata and json template to create inputs for the CWL run

        :return: JSON format sample inputs
        """
        with open(os.path.join(WORKDIR, 'input_template.json.jinja2')) as file:
            template = Template(file.read())

        sample_names = [sample_name]
        matched_normal_bams = [create_cwl_file_object(matched_normal_bam.path)]
        tumor_bams = [create_cwl_file_object(tumor_bam.path)]

        input_file = template.render(
            tumor_bams=json.dumps(tumor_bams),
            normal_bams=json.dumps(matched_normal_bams),
            sample_names=json.dumps(sample_names),
        )

        sample_input = json.loads(input_file)
        return sample_input
