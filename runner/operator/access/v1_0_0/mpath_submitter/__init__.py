import requests

from beagle.settings import MPATH_URL
from runner.operator.operator import Operator
from runner.models import PortType, Run, RunStatus, File

WORKFLOW_NAME_TO_MPATH_TYPE = {
    "access legacy MSI": "microsatellite_instability",
    "access legacy SNV": "snp_indel_variants",
    "access legacy SV": "structural_variants",
    "access legacy CNV": "copy_number_variants",
}

WORKFLOW_NAME_TO_MPATH_LOCATION_KEY = {
    "access legacy MSI": "msi_fs_location",
    "access legacy SNV": "snp_fs_location",
    "access legacy SV": "sv_fs_location",
    "access legacy CNV": "cnv_fs_location",
}



def get_sample_sheet(job_group_id):
    sample_sheet_run = Run.objects.filter(
        job_group_id=job_group_id,
        run__app__name="sample sheet",
        run__status=RunStatus.COMPLETED
    ).order_by('-created_date').first()

    sample_sheet = File.objects.filter(
        port__run=sample_sheet_run,
        port__port_type=PortType.OUTPUT
    ).first()

    return sample_sheet.path


"""
For additional information on how Voyager results are mounted on MPath server see:
https://app.gitbook.com/@mskcc-1/s/voyager/mpath/commands
"""
def juno_path_to_mpath(path):
    [_, p] = path.split("/voyager")
    return "/voyager" + p


def submit_to_mpath(workflow_name, files, sample_sheet_path):
    mpath_type = WORKFLOW_NAME_TO_MPATH_TYPE[workflow_name]
    location_key = WORKFLOW_NAME_TO_MPATH_LOCATION_KEY[workflow_name]

    data = {
        "dmp_alys_task_name": "Project_<Request_ID>",
        "ss_location": [
            juno_path_to_mpath(sample_sheet_path)
        ],
        "options": [
            mpath_type
        ],
    }
    data[location_key] = [juno_path_to_mpath(f.path) for f in files]

    payload = {
        "data": [data]
    }

    requests.post(MPATH_URL + "/ngs/", json=payload)


def get_files(runs):
    File.objects.filter(
        port__run__in=runs,
        port__run__status=RunStatus.COMPLETED,
        port__port_type=PortType.OUTPUT
    ).all()


class AccessMPathSubmitter(Operator):
    def get_jobs(self):
        runs = Run.objects.filter(id__in=self.run_ids)
        meta_run = runs[0]

        pipeline_name = meta_run.pipeline.name
        job_group_id = meta_run.job_group_id

        sample_sheet_path = get_sample_sheet(job_group_id)

        files = get_files(runs)

        submit_to_mpath(pipeline_name, files, sample_sheet_path)

        return []
