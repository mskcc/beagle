import os
import uuid
from mock import patch
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from notifier.helper import get_emails_to_notify
from notifier.models import JobGroup, JobGroupNotifier, Notifier, JiraStatus
from file_system.models import File, FileMetadata, FileGroup, FileType, Storage, StorageType


class JobGroupAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="username", password="password", email="admin@gmail.com")
        self.job_group1 = JobGroup.objects.create()
        self.job_group2 = JobGroup.objects.create()
        self.notifier = Notifier.objects.create(notifier_type="JIRA", default=True, board="TEST")
        self.job_group_notifier = JobGroupNotifier.objects.create(
            jira_id="JIRA-12", job_group=self.job_group1, notifier_type=self.notifier, status=JiraStatus.UNKNOWN
        )
        self.storage = Storage(name="test", type=StorageType.LOCAL)
        self.storage.save()
        self.file_group = FileGroup(name="Test Files", storage=self.storage)
        self.file_group.save()
        self.file_type_fastq = FileType(name="fastq")
        self.file_type_fastq.save()

    def _create_single_file(
        self,
        path,
        file_type,
        group_id,
        request_id,
        sample_id,
        lab_head_email=None,
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
        if lab_head_email:
            file_metadata[settings.LAB_HEAD_EMAIL_METADATA_KEY] = lab_head_email
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

    def _generate_jwt(self, username="username", password="password"):
        response = self.client.post("/api-token-auth/", {"username": username, "password": password}, format="json")
        return response.data["access"]

    def test_list_job_groups(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get("/v0/notifier/job-groups/", format="json")
        # Migration creates email job_group
        self.assertEqual(len(response.data["results"]), 3)

    def test_list_job_groups_by_jira_id(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.get(
            "/v0/notifier/job-groups/?jira_id=%s" % self.job_group_notifier.jira_id, format="json"
        )
        self.assertEqual(len(response.data["results"]), 1)

    def test_create_job_group(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post("/v0/notifier/job-groups/", {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @patch("notifier.tasks.send_notification.delay")
    def test_send_notification(self, send_notification):
        send_notification.return_value = False
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post(
            "/v0/notifier/send/",
            {
                "job_notifier": str(self.job_group_notifier.id),
                "notification": "SetLabelEvent",
                "arguments": {"label": "MANUAL_LABEL"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_send_notification_no_job_group(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer %s" % self._generate_jwt())
        response = self.client.post(
            "/v0/notifier/send/",
            {
                "job_notifier": str(uuid.uuid4()),
                "notification": "SetLabelEvent",
                "arguments": {"label": "MANUAL_LABEL"},
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_jira_status(self):
        response = self.client.post(
            "/v0/notifier/update/",
            {
                "timestamp": 1631020465961,
                "webhookEvent": "jira:issue_updated",
                "issue_event_type_name": "issue_generic",
                "user": {
                    "self": "http://jira.mskcc.org:8090/rest/api/2/user?username=",
                    "name": "s",
                    "key": "s",
                    "emailAddress": "s@gmail.com",
                    "avatarUrls": {},
                    "displayName": "Scruffy Scruffington",
                    "active": True,
                    "timeZone": "America/New_York",
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
                            "avatarId": 10518,
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
                                "name": "In Progress",
                            },
                        },
                    },
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
                            "toString": "CI Review Needed",
                        }
                    ],
                },
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.job_group_notifier.refresh_from_db()
        self.assertEqual(self.job_group_notifier.status, JiraStatus.CI_REVIEW_NEEDED)

    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    def test_get_emails_to_notify(self, populate_job_group_notifier_metadata):
        populate_job_group_notifier_metadata.return_value = True
        self._create_single_file(
            "/path/to/file.fastq",
            "fastq",
            str(self.file_group.id),
            "REQUEST_001",
            "SAMPLE_001",
            lab_head_email="test_email@mskcc.org",
        )
        # Test send external notification internally without notification type
        with self.settings(BEAGLE_NOTIFIER_VOYAGER_STATUS_EMAIL_TO=["me@mskcc.org"]):
            emails = get_emails_to_notify("REQUEST_001")
            self.assertEqual(len(emails), 1)
            self.assertEqual(emails[0], "me@mskcc.org")
        # Test send external notification to lab_head
        with self.settings(
            BEAGLE_NOTIFIER_VOYAGER_STATUS_EMAIL_TO=["me@mskcc.org"],
            BEAGLE_NOTIFIER_VOYAGER_STATUS_NOTIFY_EXTERNAL=["VoyagerIsProcessingWholeRequestEvent"],
        ):
            emails = get_emails_to_notify("REQUEST_001", "VoyagerIsProcessingWholeRequestEvent")
            self.assertEqual(len(emails), 2)
            self.assertListEqual(emails, ["me@mskcc.org", "test_email@mskcc.org"])
        # Test blacklisted user
        with self.settings(
            BEAGLE_NOTIFIER_VOYAGER_STATUS_EMAIL_TO=["me@mskcc.org"],
            BEAGLE_NOTIFIER_VOYAGER_STATUS_NOTIFY_EXTERNAL=["VoyagerIsProcessingWholeRequestEvent"],
            BEAGLE_NOTIFIER_VOYAGER_STATUS_BLACKLIST=["test_email@mskcc.org"],
        ):
            emails = get_emails_to_notify("REQUEST_001", "VoyagerIsProcessingWholeRequestEvent")
            self.assertEqual(len(emails), 1)
            self.assertListEqual(emails, ["me@mskcc.org"])
        # Test notification type not in list for external notifications
        with self.settings(
            BEAGLE_NOTIFIER_VOYAGER_STATUS_EMAIL_TO=["me@mskcc.org"],
            BEAGLE_NOTIFIER_VOYAGER_STATUS_NOTIFY_EXTERNAL=["VoyagerIsProcessingWholeRequestEvent"],
        ):
            emails = get_emails_to_notify("REQUEST_001", "VoyagerIsProcessingPartialRequestEvent")
            self.assertEqual(len(emails), 1)
            self.assertListEqual(emails, ["me@mskcc.org"])
