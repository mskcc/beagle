import os
import uuid
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

# from beagle_etl.jobsl import TYPES
from beagle_etl.models import JobGroup, Job, JobStatus

#
# class ETLApiTest(APITestCase):
#
#     def setUp(self):
#         self.user = User.objects.create_user(username="username",
#                                              password="password",
#                                              email='admin@gmail.com')
#         # self.storage = Storage(name="test", type=StorageType.LOCAL)
#         # self.storage.save()
#         self.job_group1 = JobGroup.objects.create()
#         self.job1 = Job.objects.create(run=TYPES['REQUEST'],
#                                        status=JobStatus.CREATED,
#                                        args={"requestId": "TEST_1"},
#                                        job_group=self.job_group1)
#         self.job_group2 = JobGroup.objects.create()
#         self.job2 = Job.objects.create(run=TYPES['REQUEST'],
#                                        status=JobStatus.CREATED,
#                                        args={settings.REQUEST_ID_METADATA_KEY: "TEST_2"},
#                                        job_group=self.job_group2)
#         self.job3 = Job.objects.create(run=TYPES['SAMPLE'],
#                                        status=JobStatus.CREATED,
#                                        args={settings.REQUEST_ID_METADATA_KEY: "TEST_3"},
#                                        job_group=self.job_group2)
#
#     def _generate_jwt(self, username="username", password="password"):
#         response = self.client.post('/api-token-auth/', {'username': username,
#                                                          'password': password},
#                                     format='json')
#         return response.data['access']

# def test_create_etl_job(self):
#     self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
#     response = self.client.post('/v0/etl/jobs/',
#                                 {
#                                     "run": "SAMPLE",
#                                     "args": {settings.REQUEST_ID_METADATA_KEY: "TEST_1"},
#                                     "job_group": str(self.job_group1.id)
#                                 },
#                                 format='json')
#     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#     self.assertEqual(response.data['job_group'], self.job_group1.id)
#
# def test_list_etl_jobs(self):
#     self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
#     response = self.client.get('/v0/etl/jobs/', format='json')
#     self.assertEqual(len(response.data['results']), 3)
#     response = self.client.get('/v0/etl/jobs/?job_group=%s' % str(self.job_group1.id),
#                                format='json')
#     self.assertEqual(len(response.data['results']), 1)
#     response = self.client.get('/v0/etl/jobs/?job_group=%s' % str(self.job_group2.id),
#                                format='json')
#     self.assertEqual(len(response.data['results']), 2)
#     response = self.client.get(
#         '/v0/etl/jobs/?job_group=%s&job_group=%s' % (str(self.job_group1.id), str(self.job_group2.id)),
#                                format='json')
#     self.assertEqual(len(response.data['results']), 3)
