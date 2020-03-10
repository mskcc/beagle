import json
import enum
import requests
from urllib.parse import urljoin
from requests.auth import HTTPBasicAuth


class JiraClient(object):
    class JiraEndpoints(enum.Enum):
        SEARCH = "/rest/api/2/search"
        CREATE = "/rest/api/2/issue"
        COMMENT = "/rest/api/2/issue/%s/comment"
        TRANSITION = "/rest/api/2/issue/%s/transitions"

    def __init__(self, url, username, password, project):
        self.username = username
        self.password = password
        self.url = url
        self.project = project

    def get_ticket(self, project_id):
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

    def create_ticket(self, summary, assignee, message):
        """
        :param summary:
        :param assignee:
        :param message:
        :return: {'id': '21402', 'key': 'RSLDEV-21', 'self': 'http://jira.mskcc.org:8090/rest/api/2/issue/21402'}
        """
        create_url = self.JiraEndpoints.CREATE.value
        body = {"fields": {"project": {"key":self.project}, "summary": summary, "issuetype": {"name": "Task"},
                           "reporter": {"name": self.username}, "assignee": {"name": assignee},
                           "priority": {"name": "Major"}, "description": message}}
        return self._post(create_url, body)

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

    def set_label(self, ticket_id, label):
        pass

    def _get(self, url, params={}, headers={}):
        default_headers = {'content-type': 'application/json'}
        headers.update(default_headers)
        response = requests.get(urljoin(self.url, url),
                                auth=HTTPBasicAuth(self.username, self.password),
                                params=params,
                                headers=headers)
        return response

    def _post(self, url, body, params={}, headers={}):
        default_headers = {'content-type': 'application/json'}
        headers.update(default_headers)
        response = requests.post(urljoin(self.url, url),
                                 auth=HTTPBasicAuth(self.username, self.password),
                                 data=json.dumps(body),
                                 params=params,
                                 headers=headers)
        return response
