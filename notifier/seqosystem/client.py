import io
import json
import enum
import requests
from urllib.parse import urljoin
from requests.auth import HTTPBasicAuth


# TODO move common methods to HTTPClient superclass
class SeqosystemClient(object):
    class SeqosystemEndpoints(enum.Enum):
        UPDATE_SAMPLE = "/api/v1/samples/%s"
        CREATE_JOB = "/api/v1/jobs"

    # TODO(aef) Add authentication when supported by seqosystem
    # https://github.com/msk-access/seqosystem/issues/9
    def __init__(self, url):
        self.url = url

    def create_job(self, job_group_id, sample_id, workflows):
        body = {
            "job_id": job_group_id,
            "sample_id": sample_id,
            "workflows": workflows
        }
        return self._post(self.SeqosystemEndpoints.CREATE_JOB.value, body)

    @staticmethod
    def parse_ticket_id(ticket_body):
        return ticket_body['key']

    def _get(self, url, params={}, headers={}):
        default_headers = {'content-type': 'application/json'}
        headers.update(default_headers)
        response = requests.get(urljoin(self.url, url),
                                auth=HTTPBasicAuth(self.username, self.password),
                                params=params,
                                headers=headers)
        return response

    def _post(self, url, body, params={}, headers={}, files={}):
        if files:
            response = requests.post(urljoin(self.url, url),
                                     auth=HTTPBasicAuth(self.username, self.password),
                                     params=params,
                                     headers=headers,
                                     files=files)
            return response
        else:
            default_headers = {'content-type': 'application/json'}
            headers.update(default_headers)
            response = requests.post(urljoin(self.url, url),
                                     auth=HTTPBasicAuth(self.username, self.password),
                                     data=json.dumps(body),
                                     params=params,
                                     headers=headers)
            return response

    def _put(self, url, body, params={}, headers={}):
        default_headers = {'content-type': 'application/json'}
        headers.update(default_headers)
        response = requests.put(urljoin(self.url, url),
                                auth=HTTPBasicAuth(self.username, self.password),
                                data=json.dumps(body),
                                params=params,
                                headers=headers)
        return response

