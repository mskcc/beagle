import uuid
from rest_framework.test import APITestCase
from file_system.models import Storage, StorageType, FileGroup
from runner.models import Pipeline, PipelineType
from django.contrib.auth.models import User

from rest_framework import status


class PipelineViewTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="username",
                                             password="password",
                                             email='admin@gmail.com')
        self.storage = Storage(name="test", type=StorageType.LOCAL)
        self.storage.save()
        self.file_group = FileGroup(name="Test Files", storage=self.storage)
        self.file_group.save()
        self.pipeline = Pipeline(name="pipeline_name",
                                 github="http://pipeline.github.com",
                                 version='v1.0',
                                 entrypoint='pipeline.cwl',
                                 pipeline_type=PipelineType.CWL,
                                 output_file_group=self.file_group,
                                 output_directory="/path/to/outputs")
        self.pipeline.save()

    def _generate_jwt(self, username="username", password="password"):
        response = self.client.post('/api-token-auth/', {'username': username,
                                                         'password': password},
                                    format='json')
        return response.data['access']

    def test_create_pipeline_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % "UNAUTHORIZED")
        response = self.client.post('/v0/run/pipelines/',
                                    {
                                        "name": "Test Pipeline",
                                        "github": "https://github.com/mskcc/roslin-cwl",
                                        "version": "master",
                                        "entrypoint": "project-workflow.cwl",
                                        "pipeline_type": PipelineType.CWL,
                                        "output_file_group": str(self.file_group.id),
                                        "output_directory": "/path/to/outputs"
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_pipeline_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.post('/v0/run/pipelines/',
                                    {
                                        "name": "Test Pipeline",
                                        "github": "https://github.com/mskcc/roslin-cwl",
                                        "version": "master",
                                        "entrypoint": "project-workflow.cwl",
                                        "pipeline_type": PipelineType.CWL,
                                        "output_file_group": str(self.file_group.id),
                                        "output_directory": "/path/to/outputs"
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_pipeline_bad_request(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.post('/v0/run/pipelines/',
                                    {},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        error_message = ["This field is required."]
        self.assertEqual(len(response_data.keys()), 6)
        self.assertEqual(response_data.get('name', None), error_message)
        self.assertEqual(response_data.get('github', None), error_message)
        self.assertEqual(response_data.get('version', None), error_message)
        self.assertEqual(response_data.get('entrypoint', None), error_message)
        self.assertEqual(response_data.get('pipeline_type', None), error_message)
        self.assertEqual(response_data.get('output_file_group', None), error_message)

    def test_create_pipeline_conflict_name(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.post('/v0/run/pipelines/',
                                    {
                                        "name": "pipeline_name",
                                        "github": "https://github.com/mskcc/roslin-cwl",
                                        "version": "master",
                                        "entrypoint": "project-workflow.cwl",
                                        "pipeline_type": PipelineType.CWL,
                                        "output_file_group": str(self.file_group.id),
                                        "output_directory": "/path/to/outputs"
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        error_message = ['pipeline with this name already exists.']
        self.assertEqual(len(response_data.keys()), 1)
        self.assertEqual(response_data.get('name', None), error_message)

    def test_get_pipeline_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % "UNAUTHORIZED")
        response = self.client.get('/v0/run/pipelines/%s/' % str(self.pipeline.id),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_pipelines_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.get('/v0/run/pipelines/%s/' % str(self.pipeline.id),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_pipeline_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.get('/v0/run/pipelines/%s/' % uuid.uuid4(),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_pipeline_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % "UNAUTHORIZED")
        response = self.client.put('/v0/run/pipelines/%s/' % str(self.pipeline.id),
                                   {
                                       "name": "pipeline_name_1"
                                   },
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_pipeline_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.patch('/v0/run/pipelines/%s/' % str(self.pipeline.id),
                                     {
                                         "name": "pipeline_name_1"
                                     },
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['name'], "pipeline_name_1")

    def test_update_pipeline_conflict_name(self):
        pipeline = Pipeline(name="some other name",
                                 github="http://pipeline.github.com",
                                 version='v1.0',
                                 entrypoint='pipeline.cwl',
                                 pipeline_type=PipelineType.CWL,
                                 output_file_group=self.file_group,
                                 output_directory="/path/to/outputs")
        pipeline.save()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.patch('/v0/run/pipelines/%s/' % str(pipeline.id),
                                     {
                                         "name": "pipeline_name"
                                     },
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_message = ['pipeline with this name already exists.']
        self.assertEqual(response.json()['name'], error_message)

    def test_update_pipeline_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.patch('/v0/run/pipelines/%s/' % str(uuid.uuid4()),
                                     {
                                         "name": "pipeline_name"
                                     },
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_pipeline_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % "UNAUTHORIZED")
        response = self.client.delete('/v0/run/pipelines/%s/' % str(self.pipeline.id),
                                      format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_pipeline_success(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.delete('/v0/run/pipelines/%s/' % str(self.pipeline.id),
                                      format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_pipeline_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.delete('/v0/run/pipelines/%s/' % str(uuid.uuid4()),
                                      format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
