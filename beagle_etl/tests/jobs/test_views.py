import os
import uuid
from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings
from django.contrib.auth.models import User
from beagle_etl.models import Job, JobStatus
from beagle_etl.jobs import TYPES
from notifier.models import JobGroup

class JobViewTest(APITestCase):

    def setUp(self):
        admin_user = User.objects.create_superuser('admin', 'sample_email', 'password')
        self.client.force_authenticate(user=admin_user)
        self.job_group1 = JobGroup(jira_id='jira_id1')
        self.job_group1.save()
        self.job_group2 = JobGroup(jira_id='jira_id2')
        self.job_group2.save()
        self.job_group3 = JobGroup(jira_id='jira_id3')
        self.job_group3.save()
        self.job_group4 = JobGroup(jira_id='jira_id4')
        self.job_group4.save()
        self.job1 = Job(args={'key1':'value1','key2':'value2','boolean_key':True,'sample_id':'sample_id1','request_id':'request_id1'}, status=JobStatus.COMPLETED, job_group=self.job_group1, run=TYPES['SAMPLE'])
        self.job1.save()
        self.job2 = Job(args={'key1':'value1','key2':'1value2','boolean_key':False,'sample_id':'sample_id2','request_id':'request_id1'}, status=JobStatus.FAILED, job_group=self.job_group2, run=TYPES['POOLED_NORMAL'])
        self.job2.save()
        self.job3 = Job(args={'key1':'value1','key2':'1value2','boolean_key':False,'sample_id':'sample_id3','request_id':'request_id1'}, status=JobStatus.FAILED, job_group=self.job_group1, run=TYPES['POOLED_NORMAL'])
        self.job3.save()
        self.job4 = Job(args={'key1':'value1','key2':'1value4','boolean_key':False,'sample_id':'sample_id4','request_id':'request_id1'}, status=JobStatus.FAILED, job_group=self.job_group3, run=TYPES['POOLED_NORMAL'])
        self.job4.save()
        self.job5 = Job(args={'key1':'value1','key2':'1value2','boolean_key':False,'sample_id':'sample_id5','request_id':'request_id2'}, status=JobStatus.FAILED, job_group=self.job_group4, run=TYPES['POOLED_NORMAL'])
        self.job5.save()
        self.api_root = '/v0/etl/jobs'

    def test_query_job_group(self):
    	response = self.client.get(self.api_root+'/?job_group='+str(self.job_group1.id))
    	self.assertEqual(len(response.json()['results']), 2)

    def test_query_job_type(self):
    	response = self.client.get(self.api_root+'/?type=POOLED_NORMAL')
    	self.assertEqual(len(response.json()['results']), 4)

    def test_query_sampleid(self):
    	response = self.client.get(self.api_root+'/?sample_id=sample_id1')
    	self.assertEqual(len(response.json()['results']), 1)

    def test_query_requestid(self):
    	response = self.client.get(self.api_root+'/?request_id=request_id1')
    	self.assertEqual(len(response.json()['results']), 4)
    	response = self.client.get(self.api_root+'/?request_id=request_id1&sample_id=sample_id1')
    	self.assertEqual(len(response.json()['results']), 1)

    def test_query_value_args(self):
    	response = self.client.get(self.api_root+'/?values_args=key1,key2')
    	self.assertEqual(len(response.json()['results']),3)

    def test_query_args(self):
    	response = self.client.get(self.api_root+'/?args=key2:1value4')
    	self.assertEqual(len(response.json()['results']), 1)
    	response = self.client.get(self.api_root+'/?args=boolean_key:False')
    	self.assertEqual(len(response.json()['results']), 4)

    def test_query_args_distribution(self):
    	response = self.client.get(self.api_root+'/?args_distribution=key2')
    	expected_result = {'1value2': 3, 'value2': 1, '1value4': 1}
    	self.assertEqual(response.json(),expected_result)

