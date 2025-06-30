"""
Tests for METADB ETL jobs
"""

import os
from mock import patch
import json
from deepdiff import DeepDiff
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from beagle_etl.models import SMILEMessage, SmileMessageStatus
from beagle_etl.models import JobGroup, JobGroupNotifier, Notifier
from beagle_etl.jobs.metadb_jobs import update_request_job, update_sample_job, new_request, update_job
from django.core.management import call_command
from file_system.models import Request, Sample, Patient, FileMetadata
from file_system.repository import FileRepository
from study.objects import StudyObject


class TestNewRequest(TestCase):
    fixtures = [
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "beagle_etl.operator.json",
        "runner.pipeline.json",
    ]

    def setUp(self):
        self.request_keys = [
            "piEmail",
            "projectManagerName",
            "labHeadName",
            "labHeadEmail",
            "investigatorName",
            "investigatorEmail",
            "dataAnalystName",
            "dataAnalystEmail",
            "otherContactEmails",
            "dataAccessEmails",
            "qcAccessEmails",
            settings.REQUEST_ID_METADATA_KEY,
            settings.PROJECT_ID_METADATA_KEY,
            settings.RECIPE_METADATA_KEY,
        ]
        self.notifier = Notifier.objects.create(notifier_type="JIRA", board="TEST")
        self.job_group = JobGroup.objects.create()
        self.job_group_notifier = JobGroupNotifier.objects.create(job_group=self.job_group, notifier_type=self.notifier)
        self.file_keys = ["R"]
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_2.file.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_2.filemetadata.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        new_request_json_path = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_2.update.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        update_sample_json_path = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_2.update_sample.json")
        call_command("loaddata", test_files_fixture, verbosity=0)
        update_request_json_path = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_request_update.json")
        with open(update_sample_json_path) as new_sample_json_file:
            self.new_sample_data = json.load(new_sample_json_file)
        self.new_sample_data_str = json.dumps(self.new_sample_data)
        with open(new_request_json_path) as new_request_json_file:
            self.new_request_data = json.load(new_request_json_file)

        self.request_data_str = json.dumps(self.new_request_data)
        with open(update_request_json_path) as update_request_json_file:
            self.update_request_data = json.load(update_request_json_file)
        self.update_request_str = json.dumps(self.update_request_data)

        test_new_request_08944_B = os.path.join(settings.TEST_FIXTURE_DIR, "08944_B_new_request.json")
        with open(test_new_request_08944_B) as new_request_08944_B:
            self.new_request = json.load(new_request_08944_B)
        self.new_request_str = json.dumps(self.new_request)

        test_new_request_14269_C = os.path.join(settings.TEST_FIXTURE_DIR, "14269_C_new_request.json")
        with open(test_new_request_14269_C) as new_request_14269_C:
            self.new_request_14269_C = json.load(new_request_14269_C)
        self.new_request_14269_C_str = json.dumps(self.new_request_14269_C)

        test_14269_C_1_update_sample = os.path.join(settings.TEST_FIXTURE_DIR, "14269_C_1_update_sample.json")
        with open(test_14269_C_1_update_sample) as update_sample_14269_C_1:
            self.update_sample_14269_C_1 = json.load(update_sample_14269_C_1)
        self.update_sample_14269_C_1_str = json.dumps(self.update_sample_14269_C_1)

        test_14269_C_1_update_sample_new_files = os.path.join(
            settings.TEST_FIXTURE_DIR, "14269_C_1_update_sample_new_files.json"
        )
        with open(test_14269_C_1_update_sample_new_files) as update_sample_14269_C_1_new_files:
            self.update_sample_14269_C_1_new_files = json.load(update_sample_14269_C_1_new_files)
        self.update_sample_14269_C_1_new_files_str = json.dumps(self.update_sample_14269_C_1_new_files)

        self.etl_user = User.objects.create_superuser("ETL", "voyager-etl@mskcc.org", "password")
        settings.ETL_USER = self.etl_user.username

    @patch("os.access")
    @patch("notifier.tasks.notifier_start")
    @patch("notifier.tasks.send_notification.delay")
    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("os.path.exists")
    def test_new_request(
        self,
        path_exists,
        populate_job_group_notifier_metadata,
        job_group_notifier_get,
        send_notification,
        notifier_start,
        access,
    ):
        path_exists.return_value = True
        populate_job_group_notifier_metadata.return_value = None
        job_group_notifier_get.return_value = self.job_group_notifier
        notifier_start.return_value = True
        send_notification.return_value = True
        access.return_value = os.R_OK
        settings.NOTIFIER_ACTIVE = False
        msg = SMILEMessage.objects.create(topic="new-request", message=self.new_request_str)
        new_request(str(msg.id))
        request = Request.objects.filter(request_id="08944_B")
        sample_1 = Sample.objects.filter(sample_id="08944_B_1")
        sample_2 = Sample.objects.filter(sample_id="08944_B_2")
        sample_3 = Sample.objects.filter(sample_id="08944_B_3")
        sample_4 = Sample.objects.filter(sample_id="08944_B_4")
        patient_1 = Patient.objects.filter(patient_id="C-MP76JR")
        patient_2 = Patient.objects.filter(patient_id="C-4LM16H")
        self.assertEqual(request.count(), 1)
        self.assertEqual(sample_1.count(), 1)
        self.assertEqual(sample_2.count(), 1)
        self.assertEqual(sample_3.count(), 1)
        self.assertEqual(sample_4.count(), 1)
        self.assertTrue(patient_1.count(), 1)
        self.assertTrue(patient_2.count(), 1)
        study = StudyObject.get_by_request("08944_B")
        self.assertIsNotNone(study)
        self.assertListEqual(list(study[0].requests), list(request.all()))
        files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "08944_B"})
        self.assertEqual(files.count(), 8)
        request = request.first()
        samples = Sample.objects.filter(sample_id__startswith="08944_B").order_by("created_date").all()
        for sample in samples:
            self.assertEqual(sample.request_id, request.request_id)
        self.assertListEqual(study[0].samples, list(samples))

    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.create_request_callback_instance")
    @patch("os.path.exists")
    def test_update_request_metadata(
        self, path_exists, request_callback, populate_job_group, send_notification, jobGroupNotifierObjectGet
    ):
        """
        Test if request metadata update is properly updating fields
        """
        request_keys = [
            "piEmail",
            "projectManagerName",
            "labHeadName",
            "labHeadEmail",
            "investigatorName",
            "investigatorEmail",
            "dataAnalystName",
            "dataAnalystEmail",
            "otherContactEmails",
            "dataAccessEmails",
            "qcAccessEmails",
        ]
        with self.settings(ETL_USER=str(self.etl_user.username)):
            path_exists.return_value = True
            request_callback.return_value = None
            populate_job_group.return_value = None
            jobGroupNotifierObjectGet.return_value = None
            send_notification.return_value = None
            msg = SMILEMessage.objects.create(topic="update_request", message=self.update_request_str)
            job_group = JobGroup()
            job_group_notifier = JobGroupNotifier(job_group=job_group)
            update_request_job(str(msg.id), job_group, job_group_notifier)
            files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "10075_D_2"})
            for file in files:
                self.assertEqual(
                    file.metadata[settings.REQUEST_ID_METADATA_KEY],
                    json.loads(self.update_request_data[-1]["requestMetadataJson"])["requestId"],
                )
                self.assertEqual(
                    file.metadata[settings.PROJECT_ID_METADATA_KEY],
                    json.loads(self.update_request_data[-1]["requestMetadataJson"])["projectId"],
                )
                self.assertEqual(
                    file.metadata[settings.RECIPE_METADATA_KEY],
                    json.loads(self.update_request_data[-1]["requestMetadataJson"])[settings.LIMS_RECIPE_METADATA_KEY],
                )
                for single_request_key in request_keys:
                    self.assertEqual(
                        file.metadata[single_request_key],
                        json.loads(self.update_request_data[-1]["requestMetadataJson"])[single_request_key],
                    )

    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.create_request_callback_instance")
    @patch("os.path.exists")
    def test_update_request_ticket(
        self, path_exists, request_callback, populate_job_group, send_notification, jobGroupNotifierObjectGet
    ):
        """
        Test that generate ticket is called properly in update request
        """
        with self.settings(ETL_USER=str(self.etl_user.username)):
            path_exists.return_value = True
            request_callback.return_value = None
            populate_job_group.return_value = None
            jobGroupNotifierObjectGet.return_value = None
            send_notification.return_value = None
            msg = SMILEMessage.objects.create(topic="update_request", message=self.update_request_str)
            job_group = JobGroup()
            job_group_notifier = JobGroupNotifier(job_group=job_group)
            request_metadata, pooled_normals = update_request_job(str(msg.id), job_group, job_group_notifier)
            files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "10075_D_2"})
            sample_names = []
            for file in files:
                sample_name = file.metadata[settings.SAMPLE_ID_METADATA_KEY]
                if sample_name not in sample_names:
                    sample_names.append(sample_name)
            self.assertEqual(len(pooled_normals), 0)
            for single_request_key in self.request_keys:
                self.assertEqual(file.metadata[single_request_key], request_metadata[single_request_key])

    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.create_request_callback_instance")
    def test_update_request_sample(
        self, request_callback, populate_job_group, send_notification, jobGroupNotifierObjectGet
    ):
        """
        Test that the samples metadata are not updated when only update request is called
        """
        with self.settings(ETL_USER=str(self.etl_user.username)):
            request_callback.return_value = None
            populate_job_group.return_value = None
            jobGroupNotifierObjectGet.return_value = None
            send_notification.return_value = None
            sample_metadata = {}
            sample_files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "10075_D_2"})
            for single_file in sample_files:
                sample_name = single_file.metadata[settings.SAMPLE_ID_METADATA_KEY]
                if sample_name not in sample_metadata:
                    sample_metadata[sample_name] = single_file.metadata
            msg = SMILEMessage.objects.create(topic="update_request", message=self.update_request_str)
            job_group = JobGroup()
            job_group_notifier = JobGroupNotifier(job_group=job_group)
            update_request_job(str(msg.id), job_group, job_group_notifier)
            files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "10075_D_2"})
            for file in files:
                metadata_keys = file.metadata.keys()
                sample_name = file.metadata[settings.SAMPLE_ID_METADATA_KEY]
                for single_metadata_key in metadata_keys:
                    current_value = file.metadata[single_metadata_key]
                    if single_metadata_key in self.file_keys:
                        continue
                    if single_metadata_key in self.request_keys:
                        if single_metadata_key == settings.REQUEST_ID_METADATA_KEY:
                            expected_value = json.loads(self.update_request_data[-1]["requestMetadataJson"])[
                                "requestId"
                            ]
                        elif single_metadata_key == settings.PROJECT_ID_METADATA_KEY:
                            expected_value = json.loads(self.update_request_data[-1]["requestMetadataJson"])[
                                "projectId"
                            ]
                        elif single_metadata_key == settings.RECIPE_METADATA_KEY:
                            expected_value = json.loads(self.update_request_data[-1]["requestMetadataJson"])[
                                settings.LIMS_RECIPE_METADATA_KEY
                            ]
                        else:
                            expected_value = json.loads(self.update_request_data[-1]["requestMetadataJson"])[
                                single_metadata_key
                            ]
                    else:
                        expected_value = sample_metadata[sample_name][single_metadata_key]
                    self.assertEqual(current_value, expected_value)

    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.create_request_callback_instance")
    def test_update_sample_preserve(
        self, request_callback, populate_job_group, send_notification, jobGroupNotifierObjectGet
    ):
        """
        Test that other samples are not modified
        """
        with self.settings(ETL_USER=str(self.etl_user.username)):
            request_callback.return_value = None
            populate_job_group.return_value = None
            jobGroupNotifierObjectGet.return_value = None
            send_notification.return_value = None
            job_group = JobGroup()
            job_group_notifier = JobGroupNotifier(job_group=job_group)
            msg = SMILEMessage.objects.create(topic="update_sample", message=self.new_sample_data_str)
            update_sample_job(str(msg.id), job_group, job_group_notifier)
            sample_files = FileRepository.filter(metadata={settings.SAMPLE_ID_METADATA_KEY: "10075_D_2_3"})
            for f in sample_files:
                self.assertEqual(f.metadata["sampleName"], "XXX002_P3_12345_L1")

    @patch("notifier.tasks.notifier_start")
    @patch("notifier.tasks.send_notification.delay")
    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("os.path.exists")
    @patch("os.access")
    def test_update_sample(
        self,
        access,
        path_exists,
        populate_job_group,
        job_group_notifier_get,
        send_notification,
        notifier_start,
    ):
        """
        Test that sample metadata is updated properly
        """
        path_exists.return_value = True
        populate_job_group.return_value = None
        send_notification.return_value = None
        job_group_notifier_get.return_value = self.job_group_notifier
        notifier_start.return_value = True
        send_notification.return_value = True
        access.return_value = os.R_OK
        settings.NOTIFIER_ACTIVE = False

        new_request_msg = SMILEMessage.objects.create(request_id="14269_C", message=self.new_request_14269_C_str)
        update_sample_msg = SMILEMessage.objects.create(
            request_id="14269_C_1", message=self.update_sample_14269_C_1_str
        )

        new_request(new_request_msg.id)
        tumor_or_normal = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: "14269_C_1"},
            values_metadata=settings.TUMOR_OR_NORMAL_METADATA_KEY,
        ).first()
        self.assertEqual(tumor_or_normal, "Normal")
        job_group = JobGroup()
        job_group_notifier = JobGroupNotifier(job_group=job_group)
        update_sample_job(update_sample_msg.id, job_group, job_group_notifier)
        tumor_or_normal = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: "14269_C_1"},
            values_metadata=settings.TUMOR_OR_NORMAL_METADATA_KEY,
        ).first()
        self.assertEqual(tumor_or_normal, "Tumor")

        files = FileRepository.filter(metadata={settings.SAMPLE_ID_METADATA_KEY: "14269_C_1"})
        self.assertEqual(len(files), 2)

        for file in files:
            old_file = FileMetadata.objects.get(file__path=file.file.path, latest=False)
            ddiff = DeepDiff(old_file.metadata, file.metadata, ignore_order=True)
            print(ddiff)
            self.assertIsNotNone(ddiff)
            self.assertEqual(ddiff["values_changed"]["root['tumorOrNormal']"]["new_value"], "Tumor")
            self.assertEqual(ddiff["values_changed"]["root['tumorOrNormal']"]["old_value"], "Normal")
            self.assertEqual(list(ddiff.keys()), ["values_changed"])

    @patch("os.access")
    @patch("notifier.tasks.notifier_start")
    @patch("notifier.tasks.send_notification.delay")
    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("os.path.exists")
    def test_update_sample_new_fastqs(
        self,
        path_exists,
        populate_job_group,
        job_group_notifier_get,
        send_notification,
        notifier_start,
        access,
    ):
        """
        Test sample updates for new fastqs
        """
        populate_job_group.return_value = None
        send_notification.return_value = None
        job_group_notifier_get.return_value = self.job_group_notifier
        notifier_start.return_value = True
        send_notification.return_value = True
        access.return_value = os.R_OK
        settings.NOTIFIER_ACTIVE = False
        path_exists.return_value = True

        new_request_msg = SMILEMessage.objects.create(request_id="14269_C", message=self.new_request_14269_C_str)
        update_sample_msg = SMILEMessage.objects.create(
            request_id="14269_C_1", message=self.update_sample_14269_C_1_new_files_str
        )

        new_request(new_request_msg.id)
        tumor_or_normal = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: "14269_C_1"},
            values_metadata=settings.TUMOR_OR_NORMAL_METADATA_KEY,
        ).first()
        self.assertEqual(tumor_or_normal, "Normal")
        job_group = JobGroup()
        job_group_notifier = JobGroupNotifier(job_group=job_group)
        update_sample_job(update_sample_msg.id, job_group, job_group_notifier)
        tumor_or_normal = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: "14269_C_1"},
            values_metadata=settings.TUMOR_OR_NORMAL_METADATA_KEY,
        ).first()
        self.assertEqual(tumor_or_normal, "Tumor")

        files = FileRepository.filter(metadata={settings.SAMPLE_ID_METADATA_KEY: "14269_C_1"})
        self.assertEqual(len(files), 2)

        for file in files:
            self.assertTrue(file.file.path.endswith("new.fastq.gz"))

        test_new_request_08944_B = os.path.join(settings.TEST_FIXTURE_DIR, "08944_B_new_request.json")
        with open(test_new_request_08944_B) as new_request_08944_B:
            self.new_request = json.load(new_request_08944_B)
        self.new_request_str = json.dumps(self.new_request)

    @patch("os.access")
    @patch("notifier.tasks.notifier_start")
    @patch("notifier.tasks.send_notification.delay")
    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("os.path.exists")
    def test_update_sample_update(
        self,
        path_exists,
        populate_job_group,
        job_group_notifier_get,
        send_notification,
        notifier_start,
        access,
    ):
        """
        Test that samples metadata is properly updated
        """
        populate_job_group.return_value = None
        send_notification.return_value = None
        job_group_notifier_get.return_value = self.job_group_notifier
        notifier_start.return_value = True
        send_notification.return_value = True
        access.return_value = os.R_OK
        settings.NOTIFIER_ACTIVE = False
        path_exists.return_value = True

        new_request_msg = SMILEMessage.objects.create(request_id="14269_C", message=self.new_request_14269_C_str)
        new_request(new_request_msg.id)
        test_14269_C_1_update_sample = os.path.join(settings.TEST_FIXTURE_DIR, "14269_C_1_update_sample.json")
        with open(test_14269_C_1_update_sample) as update_sample_14269_C_1:
            self.update_sample_14269_C_1 = json.load(update_sample_14269_C_1)
        self.update_sample_14269_C_1_str = json.dumps(self.update_sample_14269_C_1)
        msg = SMILEMessage.objects.create(
            topic="MDB_STREAM.server.cpt-gateway.cmo-sample-update",
            request_id="14269_C",
            message=self.update_sample_14269_C_1_str,
            status=SmileMessageStatus.PENDING,
        )
        update_job("14269_C")

    #     populate_job_group.return_value = None
    #     jobGroupNotifierObjectGet.return_value = None
    #     send_notification.return_value = None
    #     sample_metadata = {}
    #     file = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "10075_D_2"}).first()
    #     fastq = file.file.path
    #     for single_key in file.metadata:
    #         sample_metadata[single_key] = file.metadata[single_key]
    #     request_data = copy.deepcopy(self.new_request_data)
    #     sample_update_list = request_data["samples"]
    #     first_sample_update = sample_update_list[0]
    #     first_sample_update["libraries"][0]["runs"][0]["fastqs"] = [fastq]
    #     request_data["samples"] = [first_sample_update]
    #     for single_key in request_data:
    #         if single_key != "samples":
    #             sample_metadata[single_key] = request_data[single_key]
    #     sample_data = request_data["samples"][0]
    #     for single_key in sample_data:
    #         sample_metadata[single_key] = sample_data[single_key]
    #     sample_metadata.update(sample_data["libraries"][0])
    #     sample_metadata.update(sample_data["libraries"][0]["runs"][0])
    #     request_data_str = json.dumps(request_data)
    #     update_sample_job(request_data_str)
    #     file = FileRepository.filter(path=fastq).first()
    #     for single_key in file.metadata:
    #         if single_key in self.file_keys or single_key not in sample_metadata:
    #             continue
    #         if single_key == "ciTag":
    #             sample_name = sample_metadata["cmoSampleName"]
    #             expected_value = "s_" + sample_name.replace("-", "_")
    #         else:
    #             expected_value = sample_metadata[single_key]
    #         current_value = file.metadata[single_key]
    #         self.assertEqual(current_value, expected_value)
