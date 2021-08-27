"""
" This operator submits each downstream workflow to MPath
" An operator trigger, for each downstream workflow (MSI/CNV/SV/SNV),
" _when all runs are complete_, should be created.
" For additional information on the API and how MPath ACCESS server
" is set-up, see https://app.gitbook.com/@mskcc-1/s/voyager/mpath/
"""
import requests

from beagle.settings import MPATH_URL
from runner.operator.operator import Operator
from runner.models import PortType, Run, RunStatus, File

WORKFLOW_NAME_TO_MPATH_TYPE = {
    "access legacy MSI": "admie_microsatellite_instability",
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



def get_sample_sheet(request_id, job_group_id):
    sample_sheet_run = Run.objects.filter(
        app__name="sample sheet",
        status=RunStatus.COMPLETED,

        # Using job_group_id is better but in order to trigger MPath Submitter
        # for the massive backlog where Sample Sheet was generated in a different
        # job_group we have to use request ID
        # To trigger this for the backlog see:
        # https://app.gitbook.com/@mskcc-1/s/voyager/debugging/using-the-django-shell
        # Once the backlog is submitted this should be reverted

        # job_group_id=job_group_id,

        tags__requestId=request_id
    ).order_by('-created_date').first()

    sample_sheet = File.objects.filter(
        port__run=sample_sheet_run,
        port__port_type=PortType.OUTPUT
    ).first()

    return sample_sheet.path


def juno_path_to_mpath(path):
    [_, p] = path.split("/voyager")
    return "/voyager" + p


# This will return 400 bad request if the project already exists.
def submit_project(request_id):
    payload = {
        "data": [
            {
                "comments": "",
                "dmp_alys_task_name": "Project_" + request_id,
                "dmp_alys_task_type_cv_id": 7,
                # TODO
                "analyst_cv_id": None,
                "dmp_dms_at_id": None,
                "dmp_dms_id": None,
                "dmp_lims_id": None,
                "fellow_cv_id": None,
                "fs_location": "N/A",
                "is_clinical": 0,
                "pathologist_cv_id": None
            }
        ]
    }

    requests.post(MPATH_URL + "/ngs/projects", json=payload)


def submit_workflow(request_id, workflow_name, files, sample_sheet_path):
    mpath_type = WORKFLOW_NAME_TO_MPATH_TYPE[workflow_name]
    location_key = WORKFLOW_NAME_TO_MPATH_LOCATION_KEY[workflow_name]

    data = {
        "dmp_alys_task_name": "Project_" + request_id,
        "ss_location": [
            juno_path_to_mpath(sample_sheet_path)
        ],
        # This shouldn't be required. We can't use READONLY dirs so pointing to 
        # /voyager does not work. Talk with Anoop on what should be done.
        "fs_location": "/srv",
        "options": [
            mpath_type,
            "samples"
        ],
    }
    data[location_key] = [juno_path_to_mpath(f.path) for f in files]

    payload = {
        "data": [data]
    }

    requests.post(MPATH_URL + "/ngs/", json=payload)


def get_files(runs):
    return File.objects.filter(
        port__run__in=runs,
        port__run__status=RunStatus.COMPLETED,
        port__port_type=PortType.OUTPUT
    ).all()


class AccessMPathSubmitter(Operator):
    def get_jobs(self):
        runs = Run.objects.filter(id__in=self.run_ids)
        meta_run = runs[0]

        request_id = meta_run.metadata["requestId"]
        pipeline_name = meta_run.app.name
        job_group_id = meta_run.job_group_id

        sample_sheet_path = get_sample_sheet(request_id, job_group_id)

        files = get_files(runs)

        submit_project(request_id)
        submit_workflow(request_id, pipeline_name, files, sample_sheet_path)

        return []
