import datetime
import os
import uuid
from mock import patch
from rest_framework import status
from file_system.models import FileGroup
from runner.models import Pipeline, ProtocolType
from django.contrib.auth.models import User
from rest_framework.test import APITestCase


class SDKApiTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="username", password="password", email="admin@gmail.com")
        self.file_group = FileGroup.objects.create(name="User file-group", slug="test", owner=self.user)
        self.pipeline = Pipeline.objects.create(pipeline_type=ProtocolType.CWL,
                                                name="SDK Test Pipeline",
                                                github="http://github.com/sdk-test-pipeline.git",
                                                version="v0.1.0",
                                                entrypoint="pipeline.cwl",
                                                output_file_group=self.file_group,
                                                output_directory="/path/to/pipeline-outputs/sdk-test-pipeline"
                                                )
    def _generate_jwt(self, username="username", password="password"):
        response = self.client.post("/api-token-auth/", {"username": username, "password": password}, format="json")
        return response.data["access"]

    def test_create_sdk_operator(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post(
            "/v0/run/sdk-operator/",
            {
                "name": "Demo Operator",
                "version": "v0.1.0",
                "class_name": "DemoOperator",
                "package_name": "demo_operator",
                "github": "https://github.com/mskcc/argos-operator-v2.git",
                "pipeline_id": str(self.pipeline.id)
            },
            format="json",
        )
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)