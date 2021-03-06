import uuid
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from notifier.models import JobGroup, JobGroupNotifier, Notifier


class JobGroupAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="username",
                                             password="password",
                                             email='admin@gmail.com')
        self.job_group1 = JobGroup.objects.create(jira_id='JIRA-45')
        self.job_group2 = JobGroup.objects.create(jira_id='JIRA-54')
        self.notifier = Notifier.objects.create(notifier_type='JIRA', default=True, board='TEST')
        self.job_group_notifier = JobGroupNotifier.objects.create(jira_id='JIRA-12',
                                                                  job_group=self.job_group1,
                                                                  notifier_type=self.notifier)

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
        response = self.client.get('/v0/notifier/job-groups/?jira_id=%s' % self.job_group1.jira_id,
                                   format='json')
        self.assertEqual(len(response.data['results']), 1)

    def test_create_job_group(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.post('/v0/notifier/job-groups/',
                                    {},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_send_notification(self):
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
