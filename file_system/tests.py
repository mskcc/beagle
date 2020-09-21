import os
import uuid
from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings
from django.contrib.auth.models import User
from file_system.metadata.validator import MetadataValidator
from file_system.models import Storage, StorageType, FileGroup, File, FileType, FileMetadata


class FileTest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="username",
                                             password="password",
                                             email='admin@gmail.com')
        self.storage = Storage(name="test", type=StorageType.LOCAL)
        self.storage.save()
        self.file_group = FileGroup(name="Test Files", storage=self.storage)
        self.file_group.save()
        self.file_type_fasta = FileType(name='fasta')
        self.file_type_fasta.save()
        self.file_type_bam = FileType(name='bam')
        self.file_type_bam.save()
        self.file_type_fastq = FileType(name='fastq')
        self.file_type_fastq.save()

    def _create_single_file(self, path, file_type, group_id, request_id, sample_id):
        file_type_obj = FileType.objects.get(name=file_type)
        group_id_obj = FileGroup.objects.get(id=group_id)
        file = File(path=path, file_name=os.path.basename(path), file_type=file_type_obj, file_group=group_id_obj,
                    size=1234)
        file.save()
        file_metadata = {
            "requestId": request_id,
            "igoSampleId": sample_id
        }
        file_metadata =FileMetadata(file=file, metadata=file_metadata)
        file_metadata.save()
        return file

    def _create_files(self, file_type, amount):
        for i in range(amount):
            request_id = "request_%s" % str(i)
            sample_id = "sample_%s" % str(i)
            if file_type == 'fasta':
                file_path_R1 = "/path/to/%s_R1.%s" % (sample_id, file_type)
                self._create_single_file(file_path_R1, file_type, str(self.file_group.id), request_id, sample_id)
                file_path_R2 = "/path/to/%s_R2.%s" % (sample_id, file_type)
                self._create_single_file(file_path_R2, file_type, str(self.file_group.id), request_id, sample_id)
            else:
                file_path = "/path/to/%s.%s" % (sample_id, file_type)
                self._create_single_file(file_path, file_type, str(self.file_group.id), request_id, sample_id)

    def _generate_jwt(self, username="username", password="password"):
        response = self.client.post('/api-token-auth/', {'username': username,
                                                         'password': password},
                                    format='json')
        return response.data['access']

    def test_create_file_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % "invalid_token")
        response = self.client.post('/v0/fs/files/',
                                    {
                                        "path": "/path/to/file.fasta",
                                        "size": 1234,
                                        "file_group": str(self.file_group.id),
                                        "file_type": str(self.file_type_fasta.name)
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_file_successful(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.post('/v0/fs/files/',
                                    {
                                        "path": "/path/to/file.fasta",
                                        "size": 1234,
                                        "file_group": str(self.file_group.id),
                                        "file_type": self.file_type_fasta.name,
                                        "metadata": {
                                            "requestId": "Request_001",
                                            "igoSampleId": "igoSampleId_001"
                                        }
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['file_name'], "file.fasta")

    def test_create_file_unknown_file_type(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.post('/v0/fs/files/',
                                    {
                                        "path": "/path/to/file.fasta",
                                        "size": 1234,
                                        "file_group": str(self.file_group.id),
                                        "file_type": 'unknown',
                                        "metadata": {
                                            "requestId": "Request_001",
                                            "igoSampleId": "igoSampleId_001"
                                        }
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data['file_type'][0]), 'Unknown file_type: unknown')

    # def test_create_file_invalid_metadata(self):
        """
        Return this test when we implement metadata validation
        """
    #     self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
    #     response = self.client.post('/v0/fs/files/',
    #                                 {
    #                                     "path": "/path/to/file.fasta",
    #                                     "size": 1234,
    #                                     "file_group": str(self.file_group.id),
    #                                     "file_type": self.file_type_fasta.name,
    #                                     "metadata": {}
    #                                 },
    #                                 format='json')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_file_invalid_file_group(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.post('/v0/fs/files/',
                                    {
                                        "path": "/path/to/file.fasta",
                                        "size": 1234,
                                        "file_group": str(uuid.uuid4()),
                                        "file_type": self.file_type_fasta.name,
                                        "metadata": {}
                                    },
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_files_by_file_name(self):
        self._create_files('fasta', 30)
        self._create_files('bam', 30)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % "invalid_token")
        response = self.client.get('/v0/fs/files/', format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.get('/v0/fs/files/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 90)
        self.assertEqual(len(response.data['results']), settings.PAGINATION_DEFAULT_PAGE_SIZE)
        response = self.client.get('/v0/fs/files/?file_type=fasta', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 60)
        response = self.client.get('/v0/fs/files/?file_type=fasta&filename_regex=sample_1_', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        response = self.client.get('/v0/fs/files/?metadata=requestId:request_1', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_update_file_metadata(self):
        _file = self._create_single_file('/path/to/sample_file.bam', 'bam', str(self.file_group.id), 'request_id', 'sample_id')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.put('/v0/fs/files/%s/' % str(_file.id),
                                   {
                                       "path": _file.file_name,
                                       "size": _file.size,
                                       "file_group": str(_file.file_group.id),
                                       "file_type": _file.file_type.name,
                                       "metadata": {
                                           "requestId": "Request_001",
                                           "igoSampleId": _file.filemetadata_set.first().metadata['igoSampleId']
                                       }
                                   },
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['metadata']['requestId'], "Request_001")
        file_metadata_count = FileMetadata.objects.filter(file=str(_file.id)).count()
        self.assertEqual(file_metadata_count, 2)

    def test_patch_file_metadata(self):
        _file = self._create_single_file('/path/to/sample_file.bam', 'bam', str(self.file_group.id), 'request_id', 'sample_id')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.patch('/v0/fs/files/%s/' % str(_file.id),
                                   {
                                       "metadata": {
                                           "requestId": "Request_001",
                                       }
                                   },
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['metadata']['requestId'], "Request_001")
        self.assertEqual(response.data['metadata']['igoSampleId'], "sample_id")
        file_metadata_count = FileMetadata.objects.filter(file=str(_file.id)).count()
        self.assertEqual(file_metadata_count, 2)
        response = self.client.patch('/v0/fs/files/%s/' % str(_file.id),
                                     {
                                         "metadata": {
                                             "requestId": "Request_002",
                                         }
                                     },
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['metadata']['requestId'], "Request_002")
        self.assertEqual(response.data['metadata']['igoSampleId'], "sample_id")
        file_metadata_count = FileMetadata.objects.filter(file=str(_file.id)).count()
        self.assertEqual(file_metadata_count, 3)

    def test_batch_patch_file_metadata(self):
        first_file = self._create_single_file('/path/to/first_file.bam', 'bam', str(self.file_group.id), 'first_request_id', 'first_sample_id')
        second_file = self._create_single_file('/path/to/second_file.bam', 'bam', str(self.file_group.id), 'second_request_id', 'second_sample_id')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        patch_json = {
        "patch_files":[
            {
                "id": first_file.id,
                "patch": {
                    "metadata": {
                            "requestId": "Request_001"
                            }
                }

            },
            {
                "id": second_file.id,
                "patch": {
                    "metadata": {
                            "requestId": "Request_002"
                            }
                }

            }


        ]
        }
        response = self.client.post('/v0/fs/batch-patch-files',patch_json,format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first_file_metadata = FileMetadata.objects.order_by('file', '-version').distinct('file').filter(file=str(first_file.id)).first()
        second_file_metadata = FileMetadata.objects.order_by('file', '-version').distinct('file').filter(file=str(second_file.id)).first()
        self.assertEqual(first_file_metadata.metadata['requestId'], "Request_001")
        self.assertEqual(second_file_metadata.metadata['requestId'], "Request_002")

    def test_fail_batch_patch_file_metadata(self):
        first_file = self._create_single_file('/path/to/first_file.bam', 'bam', str(self.file_group.id), 'first_request_id', 'first_sample_id')
        second_file = self._create_single_file('/path/to/second_file.bam', 'bam', str(self.file_group.id), 'second_request_id', 'second_sample_id')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        patch_json = {
        "patch_files":[
            {
                "id": None,
                "patch": {
                    "metadata": {
                            "requestId": "Request_001"
                            }
                }

            },
            {
                "id": None,
                "patch": {
                    "metadata": {
                            "requestId": "Request_002"
                            }
                }

            }


        ]
        }
        response = self.client.post('/v0/fs/batch-patch-files',patch_json,format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_fail_batch_patch_file_metadata(self):
        first_file = self._create_single_file('/path/to/first_file.bam', 'bam', str(self.file_group.id), 'first_request_id', 'first_sample_id')
        second_file = self._create_single_file('/path/to/second_file.bam', 'bam', str(self.file_group.id), 'second_request_id', 'second_sample_id')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        patch_json = {
        "patch_files":[
            {
                "id": first_file.id,
                "patch": {
                    "metadata": {
                            "requestId": "Request_001"
                            }
                }

            },
            {
                "id": None,
                "patch": {
                    "metadata": {
                            "requestId": "Request_002"
                            }
                }

            }


        ]
        }
        response = self.client.post('/v0/fs/batch-patch-files',patch_json,format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        first_file_metadata = FileMetadata.objects.order_by('file', '-version').distinct('file').filter(file=str(first_file.id)).first()
        second_file_metadata = FileMetadata.objects.order_by('file', '-version').distinct('file').filter(file=str(second_file.id)).first()
        self.assertEqual(first_file_metadata.metadata['requestId'], "first_request_id")
        self.assertEqual(second_file_metadata.metadata['requestId'], "second_request_id")

    def test_update_file_metadata_users_update(self):
        _file = self._create_single_file('/path/to/sample_file.bam',
                                         'bam',
                                         str(self.file_group.id),
                                         'request_id',
                                         'sample_id')
        user1 = User.objects.create_user(username="user1",
                                         password="password",
                                         email='user1@gmail.com')
        user2 = User.objects.create_user(username="user2",
                                         password="password",
                                         email='user2@gmail.com')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt(username=user1.username))
        response = self.client.put('/v0/fs/files/%s/' % _file.id,
                                   {
                                       "path": _file.file_name,
                                       "size": _file.size,
                                       "file_group": str(_file.file_group.id),
                                       "file_type": _file.file_type.name,
                                       "metadata": {
                                           "requestId": "Request_001",
                                           "igoSampleId": _file.filemetadata_set.first().metadata['igoSampleId']
                                       }
                                   },
                                   format='json')
        self.assertEqual(response.data['user'], user1.username)
        self.assertEqual(response.data['metadata']['requestId'], 'Request_001')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt(username=user2.username))
        response = self.client.put('/v0/fs/files/%s/' % str(_file.id),
                                   {
                                       "path":_file.file_name,
                                       "size":_file.size,
                                       "file_group": str(_file.file_group.id),
                                       "file_type": _file.file_type.name,
                                       "metadata": {
                                           "requestId": "Request_002",
                                           "igoSampleId": _file.filemetadata_set.first().metadata['igoSampleId']
                                       }
                                   },
                                   format='json')
        self.assertEqual(response.data['user'], user2.username)
        self.assertEqual(response.data['metadata']['requestId'], 'Request_002')

        # Check listing files as well
        response = self.client.get('/v0/fs/files/?metadata=requestId:Request_001',
                                   format='json'
                                   )
        self.assertEqual(len(response.json()['results']), 0)
        response = self.client.get('/v0/fs/files/?metadata=requestId:Request_002',
                                   format='json'
                                   )
        self.assertEqual(len(response.json()['results']), 1)

    # def test_update_file_metadata_invalid(self):
        """
        Return this test when we implement metadata validation
        """
    #     _file = self._create_single_file('/path/to/sample_file.bam',
    #                                      'bam',
    #                                      str(self.file_group.id),
    #                                      'request_id',
    #                                      'sample_id')
    #     self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
    #     response = self.client.put('/v0/fs/files/%s/' % str(_file.id),
    #                                {
    #                                    "path": _file.file_name,
    #                                    "size": _file.size,
    #                                    "file_group": str(_file.file_group.id),
    #                                    "file_type": _file.file_type.name,
    #                                    "metadata": {
    #                                        "igoSampleId": _file.filemetadata_set.first().metadata['igoSampleId']
    #                                    }
    #                                },
    #                                format='json')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_file(self):
        _file = self._create_single_file('/path/to/sample_file.bam',
                                         'bam',
                                         str(self.file_group.id),
                                         'request_id',
                                         'sample_id')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.delete('/v0/fs/files/%s/' % str(_file.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        file_metadata_count = FileMetadata.objects.filter(file=str(_file.id)).count()
        self.assertEqual(file_metadata_count, 0)

    def test_list_all_metadata(self):
        _file = self._create_single_file('/path/to/sample_file.bam',
                                         'bam',
                                         str(self.file_group.id),
                                         'request_id',
                                         'sample_id')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.put('/v0/fs/files/%s/' % str(_file.id),
                                   {
                                       "path": _file.file_name,
                                       "size": _file.size,
                                       "file_group": str(_file.file_group.id),
                                       "file_type": _file.file_type.name,
                                       "metadata": {
                                           "requestId": "Request_001",
                                           "igoSampleId": _file.filemetadata_set.first().metadata['igoSampleId']
                                       }
                                   },
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get('/v0/fs/metadata/?file_id=%s' % str(_file.id), format='json')
        self.assertEqual(len(response.data['results']), 2)

    def test_list_files(self):
        self._create_single_file('/path/to/file1_R1.fastq', 'fastq', str(self.file_group.id), '1', '1s')
        self._create_single_file('/path/to/file1_R2.fastq', 'fastq', str(self.file_group.id), '1', '1s')
        self._create_single_file('/path/to/file2_R1.fastq', 'fastq', str(self.file_group.id), '2', '1s')
        self._create_single_file('/path/to/file2_R2.fastq', 'fastq', str(self.file_group.id), '2', '1s')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.get('/v0/fs/files/?path=/path/to/file1_R1.fastq',
                                   format='json'
                                   )
        self.assertEqual(len(response.json()['results']), 1)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.get('/v0/fs/files/?path=/path/to/file1_R1.fastq&values_metadata=requestId',
                                   format='json'
                                   )
        self.assertEqual(response.json()['results'][0], '1')

    def test_metadata_clean_function(self):
        test1 = "abc\tdef2"
        test2 = """
            abc\tdef!
            """
        self.assertEqual(MetadataValidator.clean_value(test1), "abc def2")
        self.assertEqual(MetadataValidator.clean_value(test2), "abc def")

    def test_query_files(self):
        self._create_single_file('/path/to/file1.fastq', 'fastq', str(self.file_group.id), '1', '3')
        self._create_single_file('/path/to/file2.fastq', 'fastq', str(self.file_group.id), '1', '2')
        self._create_single_file('/path/to/file3.fastq', 'fastq', str(self.file_group.id), '2', '1')
        self._create_single_file('/path/to/file4.fastq', 'fastq', str(self.file_group.id), '3', '4')
        self._create_single_file('/path/to/file5.fastq', 'fastq', str(self.file_group.id), '4', '3')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self._generate_jwt())
        response = self.client.get('/v0/fs/files/?metadata=requestId:1&values_metadata=requestId,igoSampleId',
                                   format='json'
                                   )
        self.assertEqual(len(response.json()['results']), 2)
        response = self.client.get('/v0/fs/files/?values_metadata=requestId,igoSampleId',
                                   format='json'
                                   )
        self.assertEqual(len(response.json()['results']), 5)




