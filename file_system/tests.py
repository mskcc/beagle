import os
import uuid
from mock import patch
from rest_framework import status
from rest_framework.test import APITestCase
from django.conf import settings
from django.contrib.auth.models import User
from beagle_etl.metadata.validator import MetadataValidator
from file_system.repository import FileRepository
from file_system.models import Storage, StorageType, FileGroup, File, FileType, FileMetadata, Sample, Request, Patient


class FileTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="username", password="password", email="admin@gmail.com")
        self.storage = Storage(name="test", type=StorageType.LOCAL)
        self.storage.save()
        self.file_group = FileGroup(name="Test Files", storage=self.storage)
        self.file_group.save()
        self.file_group_2 = FileGroup(name="New File Group", storage=self.storage)
        self.file_group_2.save()
        self.file_type_fasta = FileType(name="fasta")
        self.file_type_fasta.save()
        self.file_type_bam = FileType(name="bam")
        self.file_type_bam.save()
        self.file_type_fastq = FileType(name="fastq")
        self.file_type_fastq.save()

    def _create_single_file(
        self,
        path,
        file_type,
        group_id,
        request_id,
        sample_id,
        sample_name=None,
        cmo_sample_name=None,
        patient_id=None,
        cmo_sample_class=None,
    ):
        file_type_obj = FileType.objects.get(name=file_type)
        group_id_obj = FileGroup.objects.get(id=group_id)
        file = File(
            path=path, file_name=os.path.basename(path), file_type=file_type_obj, file_group=group_id_obj, size=1234
        )
        file.save()
        file_metadata = {settings.REQUEST_ID_METADATA_KEY: request_id, settings.SAMPLE_ID_METADATA_KEY: sample_id}
        if sample_name:
            file_metadata[settings.SAMPLE_NAME_METADATA_KEY] = sample_name
        if cmo_sample_name:
            file_metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY] = cmo_sample_name
        if patient_id:
            file_metadata[settings.PATIENT_ID_METADATA_KEY] = patient_id
        if cmo_sample_class:
            file_metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY] = cmo_sample_class

        file_metadata = FileMetadata(file=file, metadata=file_metadata)
        file_metadata.save()
        return file

    def _create_files(self, file_type, amount):
        for i in range(amount):
            request_id = "request_%s" % str(i)
            sample_id = "sample_%s" % str(i)
            file_group_id = str(self.file_group.id)
            if file_type == "fasta":
                file_path_R1 = "/path/to/%s_R1.%s" % (sample_id, file_type)
                self._create_single_file(file_path_R1, file_type, file_group_id, request_id, sample_id)
                file_path_R2 = "/path/to/%s_R2.%s" % (sample_id, file_type)
                self._create_single_file(file_path_R2, file_type, file_group_id, request_id, sample_id)
            else:
                file_path = "/path/to/%s.%s" % (sample_id, file_type)
                self._create_single_file(file_path, file_type, file_group_id, request_id, sample_id)

    def _create_files_with_details_specified(
        self, file_type, file_group_id=None, request_id=None, sample_id=None, patient_id=None
    ):
        if file_type == "fasta":
            file_path_R1 = "/path/to/%s_R1.%s" % (sample_id, file_type)
            self._create_single_file(
                file_path_R1, file_type, file_group_id, request_id, sample_id, patient_id=patient_id
            )
            file_path_R2 = "/path/to/%s_R2.%s" % (sample_id, file_type)
            self._create_single_file(
                file_path_R2, file_type, file_group_id, request_id, sample_id, patient_id=patient_id
            )
        else:
            file_path = "/path/to/%s.%s" % (sample_id, file_type)
            self._create_single_file(file_path, file_type, file_group_id, request_id, sample_id)

    def _generate_jwt(self, username="username", password="password"):
        response = self.client.post("/api-token-auth/", {"username": username, "password": password}, format="json")
        return response.data["access"]

    def test_create_file_unauthorized(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % "invalid_token")
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file.fasta",
                "size": 1234,
                "file_group": str(self.file_group.id),
                "file_type": str(self.file_type_fasta.name),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_file_too_long_sample_name(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file.fasta",
                "size": 1234,
                "file_group": str(self.file_group.id),
                "file_type": self.file_type_fasta.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: "igoSampleId_001_length_too_long_123",
                },
            },
            format="json",
        )
        self.assertContains(response, "too long", status_code=status.HTTP_400_BAD_REQUEST)

    def test_create_file_successful(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file.fasta",
                "size": 1234,
                "file_group": str(self.file_group.id),
                "file_type": self.file_type_fasta.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: "igoSampleId_001",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["file_name"], "file.fasta")
        try:
            sample = Sample.objects.get(sample_id="igoSampleId_001")
        except Sample.DoesNotExist:
            sample = None
        self.assertIsNotNone(sample)

    def test_create_file_successful_2(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file.fasta",
                "size": 1234,
                "file_group": str(self.file_group.id),
                "file_type": self.file_type_fasta.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: "igoSampleId_001",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file.fasta",
                "size": 1234,
                "file_group": str(self.file_group.id),
                "file_type": self.file_type_fasta.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: "igoSampleId_001",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_file_unknown_file_type(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file.fasta",
                "size": 1234,
                "file_group": str(self.file_group.id),
                "file_type": "unknown",
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: "igoSampleId_001",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(response.data["file_type"][0]), "Unknown file_type: unknown")

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
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file.fasta",
                "size": 1234,
                "file_group": str(uuid.uuid4()),
                "file_type": self.file_type_fasta.name,
                "metadata": {},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_files_by_file_name(self):
        self._create_files("fasta", 30)
        self._create_files("bam", 30)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % "invalid_token")
        response = self.client.get("/v0/fs/files/", format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get("/v0/fs/files/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 90)
        self.assertEqual(len(response.data["results"]), settings.PAGINATION_DEFAULT_PAGE_SIZE)
        response = self.client.get("/v0/fs/files/?file_type=fasta", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 60)
        response = self.client.get("/v0/fs/files/?file_type=fasta&filename_regex=sample_1_", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        response = self.client.get(
            "/v0/fs/files/?metadata={metadata_request_key}:request_1".format(
                metadata_request_key=settings.REQUEST_ID_METADATA_KEY
            ),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_update_file_metadata(self, populate_job_group_notifier_metadata):
        populate_job_group_notifier_metadata.return_value = True
        _file = self._create_single_file(
            "/path/to/sample_file.bam", "bam", str(self.file_group.id), "request_id", "sample_id"
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.put(
            "/v0/fs/files/%s/" % str(_file.id),
            {
                "path": _file.file_name,
                "size": _file.size,
                "file_group": str(_file.file_group.id),
                "file_type": _file.file_type.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: _file.filemetadata_set.first().metadata[
                        settings.SAMPLE_ID_METADATA_KEY
                    ],
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["metadata"][settings.REQUEST_ID_METADATA_KEY], "Request_001")
        file_metadata_count = FileMetadata.objects.filter(file=str(_file.id)).count()
        self.assertEqual(file_metadata_count, 2)

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_update_file_metadata_updatable_by_etl(self, populate_job_group_notifier_metadata):
        populate_job_group_notifier_metadata.return_value = True
        _file = self._create_single_file(
            "/path/to/sample_file.fastq",
            "fastq",
            str(self.file_group.id),
            "request_id",
            "sample_id",
            "sample_name",
            "not_updatable_by_user",
            "patient_id",
            "cmo_sample_class",
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.put(
            "/v0/fs/files/%s/" % str(_file.id),
            {
                "path": _file.file_name,
                "size": _file.size,
                "file_group": str(_file.file_group.id),
                "file_type": _file.file_type.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.CMO_SAMPLE_CLASS_METADATA_KEY: "New CMO_SAMPLE_CLASS",
                    settings.SAMPLE_ID_METADATA_KEY: _file.filemetadata_set.first().metadata[
                        settings.SAMPLE_ID_METADATA_KEY
                    ],
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_update_file_metadata_updates_request_sample_and_patient_objects(
        self, populate_job_group_notifier_metadata
    ):
        populate_job_group_notifier_metadata.return_value = True
        _file = self._create_single_file(
            "/path/to/sample_file.bam",
            "bam",
            str(self.file_group.id),
            "request_id",
            "sample_id",
            "sample_name",
            "cmo_sample_name",
            "patient_id",
        )
        user1 = User.objects.create_user(username="user1", password="password", email="user1@gmail.com")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt(username=user1.username))
        response = self.client.put(
            "/v0/fs/files/%s/" % _file.id,
            {
                "path": _file.file_name,
                "size": _file.size,
                "file_group": str(_file.file_group.id),
                "file_type": _file.file_type.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: _file.filemetadata_set.first().metadata[
                        settings.SAMPLE_ID_METADATA_KEY
                    ],
                    settings.PATIENT_ID_METADATA_KEY: "Patient_001",
                    settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor",
                    settings.INVESTIGATOR_NAME_METADATA_KEY: "Investigator Name",
                },
            },
            format="json",
        )
        self.assertEqual(response.data["user"], user1.username)
        self.assertEqual(response.data["metadata"][settings.REQUEST_ID_METADATA_KEY], "Request_001")

        _file.refresh_from_db()
        self.assertEqual(_file.request.request_id, "Request_001")
        self.assertEqual(_file.patient.patient_id, "Patient_001")
        self.assertEqual(_file.sample.tumor_or_normal, "Tumor")
        self.assertEqual(_file.request.investigator_name, "Investigator Name")

    def test_patch_file_metadata(self):
        _file = self._create_single_file(
            "/path/to/sample_file.bam", "bam", str(self.file_group.id), "request_id", "sample_id"
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.patch(
            "/v0/fs/files/%s/" % str(_file.id),
            {
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                }
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["metadata"][settings.REQUEST_ID_METADATA_KEY], "Request_001")
        self.assertEqual(response.data["metadata"][settings.SAMPLE_ID_METADATA_KEY], "sample_id")
        file_metadata_count = FileMetadata.objects.filter(file=str(_file.id)).count()
        self.assertEqual(file_metadata_count, 2)
        response = self.client.patch(
            "/v0/fs/files/%s/" % str(_file.id),
            {
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_002",
                }
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["metadata"][settings.REQUEST_ID_METADATA_KEY], "Request_002")
        self.assertEqual(response.data["metadata"][settings.SAMPLE_ID_METADATA_KEY], "sample_id")
        file_metadata_count = FileMetadata.objects.filter(file=str(_file.id)).count()
        self.assertEqual(file_metadata_count, 3)

    def test_batch_patch_file_metadata(self):
        first_file = self._create_single_file(
            "/path/to/first_file.bam", "bam", str(self.file_group.id), "first_request_id", "first_sample_id"
        )
        second_file = self._create_single_file(
            "/path/to/second_file.bam", "bam", str(self.file_group.id), "second_request_id", "second_sample_id"
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        patch_json = {
            "patch_files": [
                {"id": first_file.id, "patch": {"metadata": {settings.REQUEST_ID_METADATA_KEY: "Request_001"}}},
                {"id": second_file.id, "patch": {"metadata": {settings.REQUEST_ID_METADATA_KEY: "Request_002"}}},
            ]
        }
        response = self.client.post("/v0/fs/batch-patch-files", patch_json, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        first_file_metadata = (
            FileMetadata.objects.order_by("file", "-version").distinct("file").filter(file=str(first_file.id)).first()
        )
        second_file_metadata = (
            FileMetadata.objects.order_by("file", "-version").distinct("file").filter(file=str(second_file.id)).first()
        )
        self.assertEqual(first_file_metadata.metadata[settings.REQUEST_ID_METADATA_KEY], "Request_001")
        self.assertEqual(second_file_metadata.metadata[settings.REQUEST_ID_METADATA_KEY], "Request_002")

    def test_fail_batch_patch_file_metadata(self):
        first_file = self._create_single_file(
            "/path/to/first_file.bam", "bam", str(self.file_group.id), "first_request_id", "first_sample_id"
        )
        second_file = self._create_single_file(
            "/path/to/second_file.bam", "bam", str(self.file_group.id), "second_request_id", "second_sample_id"
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        patch_json = {
            "patch_files": [
                {"id": None, "patch": {"metadata": {settings.REQUEST_ID_METADATA_KEY: "Request_001"}}},
                {"id": None, "patch": {"metadata": {settings.REQUEST_ID_METADATA_KEY: "Request_002"}}},
            ]
        }
        response = self.client.post("/v0/fs/batch-patch-files", patch_json, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_partial_fail_batch_patch_file_metadata(self):
        first_file = self._create_single_file(
            "/path/to/first_file.bam", "bam", str(self.file_group.id), "first_request_id", "first_sample_id"
        )
        second_file = self._create_single_file(
            "/path/to/second_file.bam", "bam", str(self.file_group.id), "second_request_id", "second_sample_id"
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        patch_json = {
            "patch_files": [
                {"id": first_file.id, "patch": {"metadata": {settings.REQUEST_ID_METADATA_KEY: "Request_001"}}},
                {"id": None, "patch": {"metadata": {settings.REQUEST_ID_METADATA_KEY: "Request_002"}}},
            ]
        }
        response = self.client.post("/v0/fs/batch-patch-files", patch_json, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        first_file_metadata = (
            FileMetadata.objects.order_by("file", "-version").distinct("file").filter(file=str(first_file.id)).first()
        )
        second_file_metadata = (
            FileMetadata.objects.order_by("file", "-version").distinct("file").filter(file=str(second_file.id)).first()
        )
        self.assertEqual(first_file_metadata.metadata[settings.REQUEST_ID_METADATA_KEY], "first_request_id")
        self.assertEqual(second_file_metadata.metadata[settings.REQUEST_ID_METADATA_KEY], "second_request_id")

    def test_update_file_metadata_users_update(self):
        _file = self._create_single_file(
            "/path/to/sample_file.bam", "bam", str(self.file_group.id), "request_id", "sample_id"
        )
        user1 = User.objects.create_user(username="user1", password="password", email="user1@gmail.com")
        user2 = User.objects.create_user(username="user2", password="password", email="user2@gmail.com")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt(username=user1.username))
        response = self.client.put(
            "/v0/fs/files/%s/" % _file.id,
            {
                "path": _file.file_name,
                "size": _file.size,
                "file_group": str(_file.file_group.id),
                "file_type": _file.file_type.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: _file.filemetadata_set.first().metadata[
                        settings.SAMPLE_ID_METADATA_KEY
                    ],
                },
            },
            format="json",
        )
        self.assertEqual(response.data["user"], user1.username)
        self.assertEqual(response.data["metadata"][settings.REQUEST_ID_METADATA_KEY], "Request_001")

        _file.refresh_from_db()
        self.assertEqual(_file.request.request_id, "Request_001")

        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt(username=user2.username))
        response = self.client.put(
            "/v0/fs/files/%s/" % str(_file.id),
            {
                "path": _file.file_name,
                "size": _file.size,
                "file_group": str(_file.file_group.id),
                "file_type": _file.file_type.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_002",
                    settings.SAMPLE_ID_METADATA_KEY: _file.filemetadata_set.first().metadata[
                        settings.SAMPLE_ID_METADATA_KEY
                    ],
                },
            },
            format="json",
        )
        self.assertEqual(response.data["user"], user2.username)
        self.assertEqual(response.data["metadata"][settings.REQUEST_ID_METADATA_KEY], "Request_002")

        _file.refresh_from_db()
        self.assertEqual(_file.request.request_id, "Request_002")

        # Check listing files as well
        response = self.client.get(
            "/v0/fs/files/?metadata={request_id_key}:Request_001".format(
                request_id_key=settings.REQUEST_ID_METADATA_KEY
            ),
            format="json",
        )
        self.assertEqual(len(response.json()["results"]), 0)
        response = self.client.get(
            "/v0/fs/files/?metadata={request_id_key}:Request_002".format(
                request_id_key=settings.REQUEST_ID_METADATA_KEY
            ),
            format="json",
        )
        self.assertEqual(len(response.json()["results"]), 1)

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
    #                                        settings.SAMPLE_ID_METADATA_KEY: _file.filemetadata_set.first().metadata['igoSampleId']
    #                                    }
    #                                },
    #                                format='json')
    #     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_file(self):
        _file = self._create_single_file(
            "/path/to/sample_file.bam", "bam", str(self.file_group.id), "request_id", "sample_id"
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.delete("/v0/fs/files/%s/" % str(_file.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        file_metadata_count = FileMetadata.objects.filter(file=str(_file.id)).count()
        self.assertEqual(file_metadata_count, 0)

    def test_list_all_metadata(self):
        _file = self._create_single_file(
            "/path/to/sample_file.bam", "bam", str(self.file_group.id), "request_id", "sample_id"
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.put(
            "/v0/fs/files/%s/" % str(_file.id),
            {
                "path": _file.file_name,
                "size": _file.size,
                "file_group": str(_file.file_group.id),
                "file_type": _file.file_type.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: _file.filemetadata_set.first().metadata[
                        settings.SAMPLE_ID_METADATA_KEY
                    ],
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get("/v0/fs/metadata/?file_id=%s" % str(_file.id), format="json")
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_files(self):
        self._create_single_file("/path/to/file1_R1.fastq", "fastq", str(self.file_group.id), "1", "1s")
        self._create_single_file("/path/to/file1_R2.fastq", "fastq", str(self.file_group.id), "1", "1s")
        self._create_single_file("/path/to/file2_R1.fastq", "fastq", str(self.file_group.id), "2", "1s")
        self._create_single_file("/path/to/file2_R2.fastq", "fastq", str(self.file_group.id), "2", "1s")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get("/v0/fs/files/?path=/path/to/file1_R1.fastq", format="json")
        self.assertEqual(len(response.json()["results"]), 1)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get(
            "/v0/fs/files/?path=/path/to/file1_R1.fastq&values_metadata={request_id_key}".format(
                request_id_key=settings.REQUEST_ID_METADATA_KEY
            ),
            format="json",
        )
        self.assertEqual(response.json()["results"][0], "1")

    def test_metadata_clean_function(self):
        test1 = "abc\tdef2"
        test2 = """
            abc\tdef!
            """
        self.assertEqual(MetadataValidator.clean_value(test1), "abc def2")
        self.assertEqual(MetadataValidator.clean_value(test2), "abc def")

    def test_query_files(self):
        self._create_single_file("/path/to/file1.fastq", "fastq", str(self.file_group.id), "1", "3")
        self._create_single_file("/path/to/file2.fastq", "fastq", str(self.file_group.id), "1", "2")
        self._create_single_file("/path/to/file3.fastq", "fastq", str(self.file_group.id), "2", "1")
        self._create_single_file("/path/to/file4.fastq", "fastq", str(self.file_group.id), "3", "4")
        self._create_single_file("/path/to/file5.fastq", "fastq", str(self.file_group.id), "4", "3")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get(
            "/v0/fs/files/?metadata={request_id_key}:1&values_metadata=igoRequestId,primaryId".format(
                request_id_key=settings.REQUEST_ID_METADATA_KEY
            ),
            format="json",
        )
        self.assertEqual(len(response.json()["results"]), 2)
        response = self.client.get(
            "/v0/fs/files/?values_metadata={request_id_key},{sample_id_key}".format(
                request_id_key=settings.REQUEST_ID_METADATA_KEY, sample_id_key=settings.SAMPLE_ID_METADATA_KEY
            ),
            format="json",
        )
        self.assertEqual(len(response.json()["results"]), 5)

    def test_sample_list(self):
        sample = Sample.objects.create(sample_id="08944_B")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get("/v0/fs/sample/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_sample_update(self):
        sample = Sample.objects.create(sample_id="08944_B")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.patch(
            "/v0/fs/sample/%s/" % str(sample.id),
            {
                "redact": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("redact"), True)

    def test_sample_create(self):
        # sample = Sample.objects.create(sample_id="08944_B")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post("/v0/fs/sample/", {"sample_id": "TEST_001", "redact": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json().get("redact"), False)

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_request_list(self, populate_job_group_notifier_metadata):
        populate_job_group_notifier_metadata.return_value = True
        self._create_files_with_details_specified(
            "fastq",
            file_group_id=str(self.file_group.id),
            request_id="08944_B",
            sample_id="08944_B_1",
            patient_id="PT-001",
        )
        self._create_files_with_details_specified(
            "fastq",
            file_group_id=str(self.file_group.id),
            request_id="08944_B",
            sample_id="08944_B_2",
            patient_id="PT-001",
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get("/v0/fs/request/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 1)
        response = self.client.get("/v0/fs/sample/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()["results"]), 2)

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_request_update(self, populate_job_group_notifier_metadata):
        populate_job_group_notifier_metadata.return_value = True
        self._create_files_with_details_specified(
            "fasta",
            file_group_id=str(self.file_group.id),
            request_id="08944_B",
            sample_id="08944_B_1",
            patient_id="PT-001",
        )
        self._create_files_with_details_specified(
            "fasta",
            file_group_id=str(self.file_group.id),
            request_id="08944_B",
            sample_id="08944_B_2",
            patient_id="PT-001",
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        request = Request.objects.get(request_id="08944_B")
        response = self.client.patch(
            f"/v0/fs/request/{str(request.id)}/", {"lab_head_name": "New Lab Head Name"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "08944_B"})
        for f in files:
            self.assertEqual(files.count(), 4)
            self.assertEqual(f.metadata[settings.LAB_HEAD_NAME_METADATA_KEY], "New Lab Head Name")

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_sample_update(self, populate_job_group_notifier_metadata):
        populate_job_group_notifier_metadata.return_value = True
        self._create_files_with_details_specified(
            "fastq",
            file_group_id=str(self.file_group.id),
            request_id="08944_B",
            sample_id="08944_B_1",
            patient_id="PT-001",
        )
        self._create_files_with_details_specified(
            "fastq",
            file_group_id=str(self.file_group.id),
            request_id="08944_B",
            sample_id="08944_B_2",
            patient_id="PT-001",
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        sample = Sample.objects.get(sample_id="08944_B_1")
        response = self.client.patch(
            f"/v0/fs/sample/{str(sample.id)}/",
            {"sample_type": "New Sample Type", "tumor_or_normal": "N"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "08944_B_1"})
        for f in files:
            self.assertEqual(files.count(), 2)
            self.assertEqual(f.metadata[settings.settings.CMO_SAMPLE_CLASS_METADATA_KEY], "New Sample Type")
            self.assertEqual(f.metadata[settings.settings.TUMOR_OR_NORMAL_METADATA_KEY], "N")

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_patient_update(self, populate_job_group_notifier_metadata):
        populate_job_group_notifier_metadata.return_value = True
        self._create_files_with_details_specified(
            "fasta",
            file_group_id=str(self.file_group.id),
            request_id="08944_B",
            sample_id="08944_B_1",
            patient_id="PT-001",
        )
        self._create_files_with_details_specified(
            "fasta",
            file_group_id=str(self.file_group.id),
            request_id="08944_B",
            sample_id="08944_B_2",
            patient_id="PT-001",
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        patient = Patient.objects.get(patient_id="PT-001")
        response = self.client.patch(f"/v0/fs/patient/{str(patient.id)}/", {"sex": "M"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        files = FileRepository.filter(metadata={settings.PATIENT_ID_METADATA_KEY: "08944_B_1"})
        for f in files:
            self.assertEqual(files.count(), 4)
            self.assertEqual(f.metadata[settings.SEX_METADATA_KEY], "M")

    def test_copy_files_by_request_id_to_different_file_group(self):
        sample_1 = Sample.objects.create(sample_id="TEST_B_1")
        sample_2 = Sample.objects.create(sample_id="TEST_B_2")
        sample_3 = Sample.objects.create(sample_id="TEST_B_3")
        sample_4 = Sample.objects.create(sample_id="TEST_B_4")
        request_id = Request.objects.create(request_id="TEST_B")
        self._create_files_with_details_specified(
            "fasta", file_group_id=str(self.file_group.id), request_id="TEST_B", sample_id="TEST_B_1"
        )
        self._create_files_with_details_specified(
            "fasta", file_group_id=str(self.file_group.id), request_id="TEST_B", sample_id="TEST_B_2"
        )
        self._create_files_with_details_specified(
            "fasta", file_group_id=str(self.file_group.id), request_id="TEST_B", sample_id="TEST_B_3"
        )
        self._create_files_with_details_specified(
            "fasta", file_group_id=str(self.file_group.id), request_id="TEST_B", sample_id="TEST_B_4"
        )
        test_json = dict(
            request_id="TEST_B", file_group_from=str(self.file_group.id), file_group_to=str(self.file_group_2.id)
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post("/v0/fs/copy-files", test_json, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        files_count_original = FileRepository.filter(
            metadata={settings.REQUEST_ID_METADATA_KEY: "TEST_B"}, file_group=str(self.file_group.id)
        ).count()
        files_count_copy = FileRepository.filter(
            metadata={settings.REQUEST_ID_METADATA_KEY: "TEST_B"}, file_group=str(self.file_group_2.id)
        ).count()
        self.assertEqual(files_count_original, files_count_copy)

    def test_copy_files_by_sample_id_to_different_file_group(self):
        sample_1 = Sample.objects.create(sample_id="TEST_B_1")
        request_id = Request.objects.create(request_id="TEST_B")
        self._create_files_with_details_specified(
            "fasta", file_group_id=str(self.file_group.id), request_id="TEST_B", sample_id="TEST_B_1"
        )
        test_json = dict(
            primary_id="TEST_B_1", file_group_from=str(self.file_group.id), file_group_to=str(self.file_group_2.id)
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post("/v0/fs/copy-files", test_json, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        files_count_original = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: "TEST_B_1"}, file_group=str(self.file_group.id)
        ).count()
        files_count_copy = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: "TEST_B_1"}, file_group=str(self.file_group_2.id)
        ).count()
        self.assertEqual(files_count_original, files_count_copy)
        files_count = FileRepository.filter(metadata={settings.SAMPLE_ID_METADATA_KEY: "TEST_B_1"}).count()
        self.assertEqual(files_count, 2 * files_count_original)
