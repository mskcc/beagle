import io
import json
import enum
import requests
from urllib.parse import urljoin
from requests.auth import HTTPBasicAuth


class JiraClient(object):
    class JiraEndpoints(enum.Enum):
        SEARCH = "/rest/api/2/search"
        CREATE = "/rest/api/2/issue"
        GET = "/rest/api/2/issue/%s/"
        UPDATE = "/rest/api/2/issue/%s/"
        COMMENT = "/rest/api/2/issue/%s/comment"
        TRANSITION = "/rest/api/2/issue/%s/transitions"
        ATTACHMENT = "/rest/api/2/issue/%s/attachments"

    def __init__(self, url, username, password, project):
        self.username = username
        self.password = password
        self.url = url
        self.project = project

    def search_tickets(self, project_id):
        """
        :param project_id:
        :return: {
            "expand": "names,schema",
            "startAt": 0,
            "maxResults": 50,
            "total": 1,
            "issues": [
                {
                    "expand": "operations,versionedRepresentations,editmeta,changelog,renderedFields",
                    "id": "20359",
                    "self": "http://jira.mskcc.org:8090/rest/api/2/issue/20359",
                    "key": "RSLDEV-16",
                    "fields": ...
                }
              ]
            }
        """
        search_url = self.JiraEndpoints.SEARCH.value
        jql_url = 'project=' + self.project + ' AND summary~"' + str(project_id) + '"'
        params = {"jql": jql_url}
        headers = {'content-type': 'application/json'}
        return self._get(search_url, params=params, headers=headers)

    def get_ticket(self, ticket_id):
        get_url = self.JiraEndpoints.GET.value % ticket_id
        response = self._get(get_url)
        return response

    def create_ticket(self, summary, assignee, message):
        """
        :param summary:
        :param assignee:
        :param message:
        :return: {'id': '21402', 'key': 'RSLDEV-21', 'self': 'http://jira.mskcc.org:8090/rest/api/2/issue/21402'}
        """
        create_url = self.JiraEndpoints.CREATE.value
        body = {"fields": {"project": {"key": self.project}, "summary": summary, "issuetype": {"name": "Task"},
                           "reporter": {"name": self.username}, "assignee": {"name": assignee},
                           "priority": {"name": "Major"}, "description": message}}
        response = self._post(create_url, body)
        return response

    def update_ticket_summary(self, ticket_id, summary):
        update_url = self.JiraEndpoints.UPDATE.value % ticket_id
        body = {"fields": {"summary": summary}}
        return self._put(update_url, body)

    def update_ticket_description(self, ticket_id, message):
        update_url = self.JiraEndpoints.UPDATE.value % ticket_id
        body = {"fields": {"description": message}}
        return self._put(update_url, body)

    def update_labels(self, ticket_id, labels=[]):
        update_url = self.JiraEndpoints.UPDATE.value % ticket_id
        body = {"fields": {"labels": labels}}
        return self._put(update_url, body)

    def update_status(self, ticket_id, status_id):
        update_status_url = self.JiraEndpoints.TRANSITION.value % ticket_id
        body = {"transition": {"id": status_id}}
        response = self._post(update_status_url, body)
        return response

    def get_status_transitions(self, ticket_id):
        transitions_url = self.JiraEndpoints.TRANSITION.value % ticket_id
        response = self._get(transitions_url)
        return response

    def comment(self, ticket_id, comment):
        comment_url = self.JiraEndpoints.COMMENT.value % ticket_id
        body = {"body": comment}
        response = self._post(comment_url, body)
        return response

    def get_comments(self, ticket_id):
        comment_url = self.JiraEndpoints.COMMENT.value % ticket_id
        response = self._get(comment_url)
        return response

    def add_attachment(self, ticket_id, file_name, content):
        attachment_url = self.JiraEndpoints.ATTACHMENT.value % ticket_id
        files = {'file': (file_name, content, 'text/plain')}
        headers = {
            "X-Atlassian-Token": "nocheck"
        }
        response = self._post(attachment_url, {}, files=files, headers=headers)
        return response

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
