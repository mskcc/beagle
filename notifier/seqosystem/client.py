import io
import json
import enum
import requests
from urllib.parse import urljoin
from requests.auth import HTTPBasicAuth


# TODO move common methods to HTTPClient superclass
class SeqosystemClient(object):
    class SeqosystemEndpoints(enum.Enum):
        CREATE_JOB = "/api/v1/jobs"
        COMPLETE_JOB = "/api/v1/jobs/complete"
        FAIL_JOB = "/api/v1/jobs/fail"
        START_JOB = "/api/v1/jobs/start"

    # TODO(aef) Add authentication when supported by seqosystem
    # https://github.com/msk-access/seqosystem/issues/9
    def __init__(self, url):
        self.url = url

    def create_job(self, job_group_id, sample_id, workflows):
        body = {
            "group_id": str(job_group_id),
            "sample_id": sample_id,
            "workflows": workflows
        }
        return self._post(self.SeqosystemEndpoints.CREATE_JOB.value, body)

    def complete_job(job_group_id, pipeline_name, sample_id):
        body = {
            "group_id": str(job_group_id),
            "sample_id": sample_id,
            "workflow_name": pipeline_name,
        }
        return self._post(self.SeqosystemEndpoints.CREATE_JOB.value, body)

    def fail_job(job_group_id, pipeline_name, sample_id):
        body = {
            "group_id": str(job_group_id),
            "sample_id": sample_id,
            "workflow_name": pipeline_name,
        }
        return self._post(self.SeqosystemEndpoints.FAIL_JOB.value, body)

    def start_job(job_group_id, pipeline_name, sample_id):
        body = {
            "group_id": str(job_group_id),
            "sample_id": sample_id,
            "workflow_name": pipeline_name,
        }
        return self._post(self.SeqosystemEndpoints.START_JOB.value, body)



    # TODO(aef-) refactor these methods into client obj
    def _get(self, url, params={}, headers={}):
        default_headers = {'content-type': 'application/json'}
        headers.update(default_headers)
        response = requests.get(urljoin(self.url, url),
                                params=params,
                                headers=headers)
        return response

    def _post(self, url, body, params={}, headers={}, files={}):
        if files:
            response = requests.post(urljoin(self.url, url),
                                     params=params,
                                     headers=headers,
                                     files=files)
            return response
        else:
            default_headers = {'content-type': 'application/json'}
            headers.update(default_headers)
            response = requests.post(urljoin(self.url, url),
                                     data=json.dumps(body),
                                     params=params,
                                     headers=headers)
            return response

    def _put(self, url, body, params={}, headers={}):
        default_headers = {'content-type': 'application/json'}
        headers.update(default_headers)
        response = requests.put(urljoin(self.url, url),
                                data=json.dumps(body),
                                params=params,
                                headers=headers)
        return response

