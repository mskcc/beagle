import datetime
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
        settings.ETL_USER = "etl_user"
        self.etl_user = User.objects.create_user(
            username=settings.ETL_USER, password="password", email="etl_user@gmail.com"
        )
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
        run_date=None,
        gene_panel=None,
        created_date=None,
        modified_date=None,
    ):
        file_type_obj = FileType.objects.get(name=file_type)
        group_id_obj = FileGroup.objects.get(id=group_id)
        file = File(
            path=path, file_name=os.path.basename(path), file_type=file_type_obj, file_group=group_id_obj, size=1234
        )
        file.request_id = request_id
        file.samples = [sample_id]
        file_metadata = {settings.REQUEST_ID_METADATA_KEY: request_id, settings.SAMPLE_ID_METADATA_KEY: sample_id}
        if sample_name:
            file_metadata[settings.SAMPLE_NAME_METADATA_KEY] = sample_name
        if cmo_sample_name:
            file_metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY] = cmo_sample_name
        if patient_id:
            file.patient_id = patient_id
            file_metadata[settings.PATIENT_ID_METADATA_KEY] = patient_id
        if cmo_sample_class:
            file_metadata[settings.CMO_SAMPLE_CLASS_METADATA_KEY] = cmo_sample_class
        if run_date:
            file_metadata["runDate"] = run_date
        if gene_panel:
            file_metadata[settings.RECIPE_METADATA_KEY] = gene_panel
        file.save()
        if created_date:
            FileMetadata._meta.get_field("created_date").auto_now_add = False
            file_metadata = FileMetadata.objects.create_or_update(
                file=file, metadata=file_metadata, created_date=created_date
            )
            FileMetadata._meta.get_field("created_date").auto_now_add = True
        else:
            file_metadata = FileMetadata.objects.create_or_update(file=file, metadata=file_metadata)
        if modified_date:
            FileMetadata._meta.get_field("modified_date").auto_now = False
            file_metadata.modified_date = modified_date
            file_metadata.save()
            FileMetadata._meta.get_field("modified_date").auto_now = True
        file_metadata.refresh_from_db()
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
                    settings.PATIENT_ID_METADATA_KEY: "Patient_001",
                    settings.SAMPLE_NAME_METADATA_KEY: "sampleName_001",
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: "cmoSampleName_001",
                    settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor",
                    settings.SAMPLE_CLASS_METADATA_KEY: "sampleClass_001",
                    settings.LAB_HEAD_NAME_METADATA_KEY: "labHeadName",
                    settings.INVESTIGATOR_EMAIL_METADATA_KEY: "investigator@mskcc.org",
                    settings.INVESTIGATOR_NAME_METADATA_KEY: "Investigator",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["file_name"], "file.fasta")
        self.assertEqual(Sample.objects.filter(sample_id="igoSampleId_001").count(), 1)
        self.assertEqual(Request.objects.filter(request_id="Request_001").count(), 1)
        self.assertEqual(Patient.objects.filter(patient_id="Patient_001").count(), 1)

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
                    settings.PATIENT_ID_METADATA_KEY: "Patient_001",
                    settings.SAMPLE_NAME_METADATA_KEY: "sampleName_001",
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: "cmoSampleName_001",
                    settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor",
                    settings.SAMPLE_CLASS_METADATA_KEY: "sampleClass_001",
                    settings.LAB_HEAD_NAME_METADATA_KEY: "labHeadName",
                    settings.INVESTIGATOR_EMAIL_METADATA_KEY: "investigator@mskcc.org",
                    settings.INVESTIGATOR_NAME_METADATA_KEY: "Investigator",
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
                    settings.SAMPLE_NAME_METADATA_KEY: "sampleName_001",
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: "cmoSampleName_001",
                    settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor",
                    settings.SAMPLE_CLASS_METADATA_KEY: "sampleClass_001",
                    settings.LAB_HEAD_NAME_METADATA_KEY: "labHeadName",
                    settings.INVESTIGATOR_EMAIL_METADATA_KEY: "investigator@mskcc.org",
                    settings.INVESTIGATOR_NAME_METADATA_KEY: "Investigator",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Sample.objects.filter(sample_id="igoSampleId_001").count(), 1)
        self.assertEqual(Request.objects.filter(request_id="Request_001").count(), 1)
        self.assertEqual(Patient.objects.filter(patient_id="Patient_001").count(), 1)

    def test_crete_files_count_sample_patient_request(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file_R1.fastq",
                "size": 1234,
                "file_group": str(self.file_group.id),
                "file_type": self.file_type_fasta.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: "igoSampleId_001",
                    settings.PATIENT_ID_METADATA_KEY: "Patient_001",
                    settings.SAMPLE_NAME_METADATA_KEY: "sampleName_001",
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: "cmoSampleName_001",
                    settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor",
                    settings.SAMPLE_CLASS_METADATA_KEY: "sampleClass_001",
                    settings.LAB_HEAD_NAME_METADATA_KEY: "labHeadName",
                    settings.INVESTIGATOR_EMAIL_METADATA_KEY: "investigator@mskcc.org",
                    settings.INVESTIGATOR_NAME_METADATA_KEY: "Investigator",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file_R2.fastq",
                "size": 1234,
                "file_group": str(self.file_group.id),
                "file_type": self.file_type_fasta.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: "igoSampleId_001",
                    settings.PATIENT_ID_METADATA_KEY: "Patient_001",
                    settings.SAMPLE_NAME_METADATA_KEY: "sampleName_001",
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: "cmoSampleName_001",
                    settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor",
                    settings.SAMPLE_CLASS_METADATA_KEY: "sampleClass_001",
                    settings.LAB_HEAD_NAME_METADATA_KEY: "labHeadName",
                    settings.INVESTIGATOR_EMAIL_METADATA_KEY: "investigator@mskcc.org",
                    settings.INVESTIGATOR_NAME_METADATA_KEY: "Investigator",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Sample.objects.filter(sample_id="igoSampleId_001").count(), 1)
        self.assertEqual(Request.objects.filter(request_id="Request_001").count(), 1)
        self.assertEqual(Patient.objects.filter(patient_id="Patient_001").count(), 1)

    def test_create_file_with_update_request_metadata(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file_R1.fastq",
                "size": 1234,
                "file_group": str(self.file_group.id),
                "file_type": self.file_type_fasta.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: "igoSampleId_001",
                    settings.PATIENT_ID_METADATA_KEY: "Patient_001",
                    settings.SAMPLE_NAME_METADATA_KEY: "sampleName_001",
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: "cmoSampleName_001",
                    settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor",
                    settings.SAMPLE_CLASS_METADATA_KEY: "sampleClass_001",
                    settings.LAB_HEAD_NAME_METADATA_KEY: "labHeadName",
                    settings.INVESTIGATOR_EMAIL_METADATA_KEY: "investigator@mskcc.org",
                    settings.INVESTIGATOR_NAME_METADATA_KEY: "Investigator",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        file_id_1 = response.json()["id"]
        response = self.client.post(
            "/v0/fs/files/",
            {
                "path": "/path/to/file_R2.fastq",
                "size": 1234,
                "file_group": str(self.file_group.id),
                "file_type": self.file_type_fasta.name,
                "metadata": {
                    settings.REQUEST_ID_METADATA_KEY: "Request_001",
                    settings.SAMPLE_ID_METADATA_KEY: "igoSampleId_001",
                    settings.SAMPLE_NAME_METADATA_KEY: "sampleName_001",
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: "cmoSampleName_001",
                    settings.TUMOR_OR_NORMAL_METADATA_KEY: "Tumor",
                    settings.SAMPLE_CLASS_METADATA_KEY: "sampleClass_001",
                    settings.LAB_HEAD_NAME_METADATA_KEY: "labHeadName new",
                    settings.INVESTIGATOR_EMAIL_METADATA_KEY: "investigator@mskcc.org",
                    settings.INVESTIGATOR_NAME_METADATA_KEY: "Investigator",
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        file_id_2 = response.json()["id"]
        self.assertEqual(Sample.objects.filter(sample_id="igoSampleId_001").count(), 1)
        self.assertEqual(Request.objects.filter(request_id="Request_001").count(), 2)
        self.assertEqual(Patient.objects.filter(patient_id="Patient_001").count(), 1)
        file_1 = File.objects.get(id=file_id_1)
        file_2 = File.objects.get(id=file_id_2)
        request = Request.objects.get(request_id="Request_001", latest=True)
        self.assertEqual(str(file_1.get_request().pk), str(request.id))
        self.assertEqual(str(file_2.get_request().pk), str(request.id))
        self.assertEqual(file_1.get_request().lab_head_name, "labHeadName new")
        self.assertEqual(file_2.get_request().lab_head_name, "labHeadName new")

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
        self.assertEqual(_file.get_request().request_id, "Request_001")
        self.assertEqual(_file.get_patient().patient_id, "Patient_001")
        self.assertEqual(_file.get_samples().first().tumor_or_normal, "Tumor")
        self.assertEqual(_file.get_request().investigator_name, "Investigator Name")

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

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_batch_patch_file_metadata(self, populate_job_group_notifier_metadata):
        populate_job_group_notifier_metadata.return_value = None
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

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_partial_fail_batch_patch_file_metadata(self, populate_job_group_notifier_metadata):
        populate_job_group_notifier_metadata.return_value = None
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
        response = self.client.post("/v0/fs/batch-patch-files/", patch_json, format="json")
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
        self.assertEqual(_file.get_request().request_id, "Request_001")

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
        self.assertEqual(_file.get_request().request_id, "Request_002")

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
            f"/v0/fs/files/?path=/path/to/file1_R1.fastq&values_metadata={settings.REQUEST_ID_METADATA_KEY},{settings.SAMPLE_ID_METADATA_KEY}",
            format="json",
        )
        self.assertEqual(response.json()["results"][0][f"metadata__{settings.REQUEST_ID_METADATA_KEY}"], "1")
        self.assertEqual(response.json()["results"][0][f"metadata__{settings.SAMPLE_ID_METADATA_KEY}"], "1s")

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

    def test_get_files_created_date(self):
        request_id = "08944_B"
        sample_id_1 = "08944_B_1"
        file_path_R1_1 = f"/path/to/{sample_id_1}_R1.fastq"
        file_path_R2_1 = f"/path/to/{sample_id_1}_R2.fastq"
        created_date = datetime.datetime(2025, 1, 1, 0, 0, 0)
        modified_date = datetime.datetime(2025, 1, 1, 0, 0, 0)
        self._create_single_file(
            file_path_R1_1,
            "fastq",
            str(self.file_group.id),
            request_id,
            sample_id_1,
            run_date="25-01-01",
            created_date=created_date,
            modified_date=modified_date,
        )
        created_date = datetime.datetime(2025, 1, 1, 0, 0, 2)
        modified_date = datetime.datetime(2025, 1, 1, 0, 0, 2)
        self._create_single_file(
            file_path_R2_1,
            "fastq",
            str(self.file_group.id),
            request_id,
            sample_id_1,
            run_date="25-01-01",
            created_date=created_date,
            modified_date=modified_date,
        )
        query_date = datetime.datetime(2025, 1, 1, 0, 0, 1)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get(
            f"/v0/fs/files/?metadata={settings.REQUEST_ID_METADATA_KEY}:{request_id}&created_date_gt={query_date.isoformat()}",
            format="json",
        )
        self.assertEqual(response.json()["count"], 1)

    def test_get_files_modified_date(self):
        request_id = "08944_B"
        sample_id_1 = "08944_B_1"
        file_path_R1_1 = f"/path/to/{sample_id_1}_R1.fastq"
        file_path_R2_1 = f"/path/to/{sample_id_1}_R2.fastq"
        created_date = datetime.datetime(2025, 1, 1, 0, 0, 0)
        modified_date = datetime.datetime(2025, 1, 1, 0, 0, 0)
        self._create_single_file(
            file_path_R1_1,
            "fastq",
            str(self.file_group.id),
            request_id,
            sample_id_1,
            created_date=created_date,
            modified_date=modified_date,
        )
        created_date = datetime.datetime(2025, 1, 1, 0, 0, 2)
        modified_date = datetime.datetime(2025, 1, 1, 0, 0, 2)
        self._create_single_file(
            file_path_R2_1,
            "fastq",
            str(self.file_group.id),
            request_id,
            sample_id_1,
            created_date=created_date,
            modified_date=modified_date,
        )
        query_date = datetime.datetime(2025, 1, 1, 0, 0, 1)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get(
            f"/v0/fs/files/?metadata={settings.REQUEST_ID_METADATA_KEY}:{request_id}&modified_date_lt={query_date.isoformat()}",
            format="json",
        )
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["path"], file_path_R1_1)

    def test_get_files_return_value_with_datetime(self):
        request_id = "08944_B"
        sample_id_1 = "08944_B_1"
        file_path_R1_1 = f"/path/to/{sample_id_1}_R1.fastq"
        file_path_R2_1 = f"/path/to/{sample_id_1}_R2.fastq"
        created_date = datetime.datetime(2025, 1, 1, 0, 0, 0)
        modified_date = datetime.datetime(2025, 1, 1, 0, 0, 0)
        self._create_single_file(
            file_path_R1_1,
            "fastq",
            str(self.file_group.id),
            request_id,
            sample_id_1,
            run_date="25-01-01",
            created_date=created_date,
            modified_date=modified_date,
        )
        self._create_single_file(
            file_path_R2_1,
            "fastq",
            str(self.file_group.id),
            request_id,
            sample_id_1,
            run_date="25-01-01",
            created_date=created_date,
            modified_date=modified_date,
        )
        sample_id_2 = "08944_B_2"
        file_path_R1_2 = f"/path/to/{sample_id_2}_R1.fastq"
        file_path_R2_2 = f"/path/to/{sample_id_2}_R2.fastq"
        created_date_2 = datetime.datetime(2025, 2, 1, 0, 0, 0)
        modified_date_2 = datetime.datetime(2025, 2, 2, 0, 0, 0)
        self._create_single_file(
            file_path_R1_2,
            "fastq",
            str(self.file_group.id),
            request_id,
            sample_id_2,
            run_date="25-01-01",
            created_date=created_date_2,
            modified_date=modified_date_2,
        )
        self._create_single_file(
            file_path_R2_2,
            "fastq",
            str(self.file_group.id),
            request_id,
            sample_id_2,
            run_date="25-01-01",
            created_date=created_date_2,
            modified_date=modified_date_2,
        )

        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        # Test samples created after 2025/1/1
        query_date = datetime.datetime(2024, 12, 31, 23, 23, 59)
        response = self.client.get(
            f"/v0/fs/files/?metadata={settings.REQUEST_ID_METADATA_KEY}:{request_id}&values_metadata=primaryId&created_date_gt={query_date.isoformat()}",
            format="json",
        )
        self.assertEqual(response.json()["count"], 2)
        response = self.client.get(
            f"/v0/fs/files/?metadata={settings.REQUEST_ID_METADATA_KEY}:{request_id}&values_metadata=primaryId&created_date_gt={query_date.isoformat()}",
            format="json",
        )
        # Test samples modified after 2025/2/15
        query_date = datetime.datetime(2025, 1, 15, 0, 0, 0)
        response = self.client.get(
            f"/v0/fs/files/?metadata={settings.REQUEST_ID_METADATA_KEY}:{request_id}&values_metadata=primaryId&modified_date_gt={query_date.isoformat()}",
            format="json",
        )
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["metadata__primaryId"], "08944_B_2")
        # Test samples modified before 2025/2/15
        response = self.client.get(
            f"/v0/fs/files/?metadata={settings.REQUEST_ID_METADATA_KEY}:{request_id}&values_metadata=primaryId,runDate&distinct_metadata=primaryId&modified_date_lt={query_date.isoformat()}",
            format="json",
        )
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["metadata__primaryId"], "08944_B_1")

    def test_multiple_values_metadata(self):
        request_id = "08944_B"
        for i in range(100):
            request_id = "08944_B"
            sample_id = f"08944_B_{i}"
            file_path_R1 = f"/path/to/{sample_id}_R1.fastq"
            file_path_R2 = f"/path/to/{sample_id}_R2.fastq"
            created_date = datetime.datetime(2025, 1, 1, 0, 0, 0)
            modified_date = datetime.datetime(2025, 1, 1, 0, 0, 0)
            self._create_single_file(
                file_path_R1,
                "fastq",
                str(self.file_group.id),
                request_id,
                sample_id,
                run_date="25-01-01",
                created_date=created_date,
                modified_date=modified_date,
            )
            self._create_single_file(
                file_path_R2,
                "fastq",
                str(self.file_group.id),
                request_id,
                sample_id,
                run_date="25-01-01",
                created_date=created_date,
                modified_date=modified_date,
            )
        query_date = datetime.datetime(2024, 12, 31, 23, 23, 59)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get(
            f"/v0/fs/files/?values_metadata=primaryId&created_date_gt={query_date.isoformat()}&size=200",
            format="json",
        )
        self.assertEqual(response.json()["count"], 100)

    def random_date(self, start, end):
        import pytz
        from random import randrange
        from datetime import timedelta

        """
        This function will return a random datetime between two datetime
        objects.
        """
        delta = end - start
        int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
        random_second = randrange(int_delta)
        timezone = pytz.timezone("America/New_York")
        random_time = start + timedelta(seconds=random_second)
        try:
            localized_time = timezone.localize(random_time)
        except pytz.exceptions.NonExistentTimeError:
            return self.random_date(start, end)
        return localized_time

    def test_file_repository_distinct(self):
        """
        TODO: This test works, try to find edgecase from production
        """
        start_date = datetime.datetime(2021, 1, 1, 0, 0, 0)
        end_date = datetime.datetime(2025, 1, 1, 0, 0, 0)
        gene_panel = "IMPACT505"
        import random
        import string

        for i in range(100):
            request_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            sample_id = f"{request_id}_{i}"
            file_path_R1 = f"/path/to/{sample_id}_R1.fastq"
            file_path_R2 = f"/path/to/{sample_id}_R2.fastq"
            run_date_1 = self.random_date(start_date, end_date)
            self._create_single_file(
                file_path_R1,
                "fastq",
                str(self.file_group.id),
                request_id,
                sample_id,
                run_date=run_date_1.strftime("%Y-%m-%d"),
                gene_panel=gene_panel,
                created_date=self.random_date(start_date, end_date),
                modified_date=self.random_date(start_date, end_date),
            )
            run_date_2 = self.random_date(start_date, end_date)
            self._create_single_file(
                file_path_R2,
                "fastq",
                str(self.file_group.id),
                request_id,
                sample_id,
                run_date=run_date_2.strftime("%Y-%m-%d"),
                gene_panel=gene_panel,
                created_date=self.random_date(start_date, end_date),
                modified_date=self.random_date(start_date, end_date),
            )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get(
            f"/v0/fs/files/?distinct_metadata=primaryId&metadata=genePanel:{gene_panel}&values_metadata=primaryId,runDate",
            format="json",
        )
        self.assertEqual(response.json()["count"], 100)

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

    def test_sample_update_cas_qc_notes(self):
        sample = Sample.objects.create(sample_id="08944_B")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.patch(
            "/v0/fs/sample/%s/" % str(sample.id),
            {
                "igo_qc_notes": "QC Failed",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("igo_qc_notes"), "QC Failed")

    def test_sample_create(self):
        # TODO: Fix this
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
