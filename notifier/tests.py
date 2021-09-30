import uuid
from mock import patch
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from notifier.models import JobGroup, JobGroupNotifier, Notifier, JiraStatus


class JobGroupAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="username",
                                             password="password",
                                             email='admin@gmail.com')
        self.job_group1 = JobGroup.objects.create()
        self.job_group2 = JobGroup.objects.create()
        self.notifier = Notifier.objects.create(notifier_type='JIRA', default=True, board='TEST')
        self.job_group_notifier = JobGroupNotifier.objects.create(jira_id='JIRA-12',
                                                                  job_group=self.job_group1,
                                                                  notifier_type=self.notifier,
                                                                  status=JiraStatus.UNKNOWN)

    def _generate_jwt(self, username="username", password="password"):
        response = self.client.post('/api-token-auth/', {'username': username,
                                                         'password': password},
                                    format='json')
        return response.data['access']

    def test_list_job_groups(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.get('/v0/notifier/job-groups/', format='json')
        # Migration creates email job_group
        self.assertEqual(len(response.data['results']), 3)

    def test_list_job_groups_by_jira_id(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.get('/v0/notifier/job-groups/?jira_id=%s' % self.job_group_notifier.jira_id,
                                   format='json')
        self.assertEqual(len(response.data['results']), 1)

    def test_create_job_group(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.post('/v0/notifier/job-groups/',
                                    {},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("notifier.tasks.send_notification.delay")
    def test_send_notification(self, send_notification):
        send_notification.return_value = False
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.post('/v0/notifier/send/',
                                    {
                                        "job_notifier": str(self.job_group_notifier.id),
                                        "notification": "SetLabelEvent",
                                        "arguments": {"label": "MANUAL_LABEL"}
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_send_notification_no_job_group(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.post('/v0/notifier/send/',
                                    {
                                        "job_notifier": str(uuid.uuid4()),
                                        "notification": "SetLabelEvent",
                                        "arguments": {"label": "MANUAL_LABEL"}
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_jira_status(self):
        response = self.client.post('/v0/notifier/update/',
                                    {
                                        "timestamp": 1631020465961,
                                        "webhookEvent": "jira:issue_updated",
                                        "issue_event_type_name": "issue_generic",
                                        "user": {
                                            "self": "http://jira.mskcc.org:8090/rest/api/2/user?username=",
                                            "name": "s",
                                            "key": "s",
                                            "emailAddress": "s@gmail.com",
                                            "avatarUrls": {
                                            },
                                            "displayName": "Scruffy Scruffington",
                                            "active": True,
                                            "timeZone": "America/New_York"
                                        },
                                        "issue": {
                                            "id": "55631",
                                            "self": "http://jira.mskcc.org:8090/rest/api/2/issue/55631",
                                            "key": "JIRA-12",
                                            "fields": {
                                                "issuetype": {
                                                    "self": "http://jira.mskcc.org:8090/rest/api/2/issuetype/3",
                                                    "id": "3",
                                                    "description": "A task that needs to be done.",
                                                    "iconUrl": "http://jira.mskcc.org:8090/secure/viewavatar?size=xsmall&avatarId=10518&avatarType=issuetype",
                                                    "name": "Task",
                                                    "subtask": False,
                                                    "avatarId": 10518
                                                },
                                                "assignee": None,
                                                "updated": "2021-09-07T09:14:25.958-0400",
                                                "status": {
                                                    "self": "http://jira.mskcc.org:8090/rest/api/2/status/10619",
                                                    "description": "CI Review Needed",
                                                    "iconUrl": "http://jira.mskcc.org:8090/images/icons/statuses/generic.png",
                                                    "name": "CI Review Needed",
                                                    "id": "10619",
                                                    "statusCategory": {
                                                        "self": "http://jira.mskcc.org:8090/rest/api/2/statuscategory/4",
                                                        "id": 4,
                                                        "key": "indeterminate",
                                                        "colorName": "yellow",
                                                        "name": "In Progress"
                                                    }
                                                }
                                            }
                                        },
                                        "changelog": {
                                            "id": "554271",
                                            "items": [
                                                {
                                                    "field": "status",
                                                    "fieldtype": "jira",
                                                    "from": "10620",
                                                    "fromString": "Pipeline Completed; No Failures",
                                                    "to": "10619",
                                                    "toString": "CI Review Needed"
                                                }
                                            ]
                                        }
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job_group_notifier.refresh_from_db()
        self.assertEqual(self.job_group_notifier.status, JiraStatus.CI_REVIEW_NEEDED)
