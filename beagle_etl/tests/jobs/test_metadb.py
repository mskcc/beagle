"""
Tests for METADB ETL jobs
"""

import os
from mock import patch
import json
from deepdiff import DeepDiff
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from beagle_etl.models import SMILEMessage, SmileMessageStatus
from beagle_etl.models import JobGroup, JobGroupNotifier, Notifier
from beagle_etl.jobs.metadb_jobs import update_request_job, update_sample_job, new_request
from django.core.management import call_command
from file_system.models import Request, Sample, Patient, FileMetadata, FileGroup
from file_system.repository import FileRepository
from study.objects import StudyObject


class TestSmileMessages(TestCase):
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
        self.file_group_id = "1a1b29cf-3bc2-4f6c-b376-d4c5d701166a"
        settings.ETL_USER = self.etl_user.username
        settings.NOTIFIER_ACTIVE = False

    @patch("os.access")
    @patch("notifier.tasks.notifier_start")
    @patch("notifier.tasks.send_notification.delay")
    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("os.path.exists")
    @patch("beagle_etl.jobs.helper_jobs.calculate_checksum.delay")
    @override_settings(IMPORT_FILE_GROUP="1a1b29cf-3bc2-4f6c-b376-d4c5d701166a")
    def test_new_request(
        self,
        calculate_checksum,
        path_exists,
        populate_job_group_notifier_metadata,
        job_group_notifier_get,
        send_notification,
        notifier_start,
        access,
    ):
        calculate_checksum.return_value = None
        path_exists.return_value = True
        populate_job_group_notifier_metadata.return_value = None
        job_group_notifier_get.return_value = self.job_group_notifier
        notifier_start.return_value = True
        send_notification.return_value = True
        access.return_value = os.R_OK
        msg = SMILEMessage.objects.create(
            topic="new-request", request_id="08944_B", gene_panel="", message=self.new_request_str
        )
        msg.in_progress()
        new_request(str(msg.id))
        msg.refresh_from_db()
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
        files = FileRepository.filter(
            metadata={settings.REQUEST_ID_METADATA_KEY: "08944_B"}, file_group=self.file_group_id
        )
        self.assertEqual(msg.status, SmileMessageStatus.COMPLETED)
        self.assertEqual(files.count(), 8)
        request = request.first()
        samples = Sample.objects.filter(sample_id__startswith="08944_B").order_by("created_date").all()
        for sample in samples:
            self.assertEqual(sample.request_id, request.request_id)
        self.assertListEqual(study[0].samples, list(samples))

        msg.refresh_from_db()
        self.assertEqual(msg.status, SmileMessageStatus.COMPLETED)

    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.create_request_callback_instance")
    @patch("os.path.exists")
    @patch("beagle_etl.jobs.helper_jobs.calculate_checksum.delay")
    def test_update_request_metadata(
        self,
        calculate_checksum,
        path_exists,
        request_callback,
        populate_job_group,
        send_notification,
        jobGroupNotifierObjectGet,
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
            calculate_checksum.return_value = None
            path_exists.return_value = True
            request_callback.return_value = None
            populate_job_group.return_value = None
            jobGroupNotifierObjectGet.return_value = None
            send_notification.return_value = None
            msg = SMILEMessage.objects.create(topic="update_request", message=self.update_request_str)
            msg.in_progress()
            update_request_job(str(msg.id))
            files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "10075_D"})
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

            msg.refresh_from_db()
            self.assertEqual(msg.status, SmileMessageStatus.COMPLETED)

    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.create_request_callback_instance")
    @patch("os.path.exists")
    @patch("beagle_etl.jobs.helper_jobs.calculate_checksum.delay")
    def test_update_request_ticket(
        self,
        calculate_checksum,
        path_exists,
        request_callback,
        populate_job_group,
        send_notification,
        jobGroupNotifierObjectGet,
    ):
        """
        Test that generate ticket is called properly in update request
        """
        with self.settings(ETL_USER=str(self.etl_user.username)):
            calculate_checksum.return_value = None
            path_exists.return_value = True
            request_callback.return_value = None
            populate_job_group.return_value = None
            jobGroupNotifierObjectGet.return_value = None
            send_notification.return_value = None
            msg = SMILEMessage.objects.create(topic="update_request", message=self.update_request_str)
            msg.in_progress()
            update_request_job(str(msg.id))
            files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "10075_D_2"})
            sample_names = []
            for file in files:
                sample_name = file.metadata[settings.SAMPLE_ID_METADATA_KEY]
                if sample_name not in sample_names:
                    sample_names.append(sample_name)

            msg.refresh_from_db()
            self.assertEqual(msg.status, SmileMessageStatus.COMPLETED)

    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.create_request_callback_instance")
    @patch("beagle_etl.jobs.helper_jobs.calculate_checksum.delay")
    def test_update_request_sample(
        self, calculate_checksum, request_callback, populate_job_group, send_notification, jobGroupNotifierObjectGet
    ):
        """
        Test that the samples metadata are not updated when only update request is called
        """
        with self.settings(ETL_USER=str(self.etl_user.username)):
            calculate_checksum.return_value = None
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
            msg.in_progress()
            update_request_job(str(msg.id))
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

            msg.refresh_from_db()
            self.assertEqual(msg.status, SmileMessageStatus.COMPLETED)

    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.create_request_callback_instance")
    @patch("os.path.exists")
    @patch("os.access")
    @patch("beagle_etl.jobs.helper_jobs.calculate_checksum.delay")
    @override_settings(IMPORT_FILE_GROUP="1a1b29cf-3bc2-4f6c-b376-d4c5d701166a")
    def test_update_sample_preserve(
        self,
        calculate_checksum,
        access,
        path_exist,
        request_callback,
        populate_job_group,
        send_notification,
        jobGroupNotifierObjectGet,
    ):
        """
        Test that other samples are not modified
        """
        with self.settings(ETL_USER=str(self.etl_user.username)):
            calculate_checksum.return_value = None
            access.return_value = os.R_OK
            path_exist.return_value = True
            request_callback.return_value = None
            populate_job_group.return_value = None
            jobGroupNotifierObjectGet.return_value = None
            send_notification.return_value = None
            msg = SMILEMessage.objects.create(topic="update_sample", message=self.new_sample_data_str)
            msg.in_progress()
            update_sample_job(str(msg.id))
            sample_files = FileRepository.filter(metadata={settings.SAMPLE_ID_METADATA_KEY: "10075_D_2"})
            for f in sample_files:
                self.assertEqual(f.metadata["sampleName"], "TestSample001")

            msg.refresh_from_db()
            self.assertEqual(msg.status, SmileMessageStatus.COMPLETED)

    @patch("notifier.tasks.notifier_start")
    @patch("notifier.tasks.send_notification.delay")
    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("os.path.exists")
    @patch("os.access")
    @patch("beagle_etl.jobs.helper_jobs.calculate_checksum.delay")
    @override_settings(IMPORT_FILE_GROUP="1a1b29cf-3bc2-4f6c-b376-d4c5d701166a")
    def test_update_sample(
        self,
        calculate_checksum,
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
        calculate_checksum.return_value = None
        path_exists.return_value = True
        populate_job_group.return_value = None
        send_notification.return_value = None
        job_group_notifier_get.return_value = self.job_group_notifier
        notifier_start.return_value = True
        send_notification.return_value = True
        access.return_value = os.R_OK
        settings.NOTIFIER_ACTIVE = False

        new_request_msg = SMILEMessage.objects.create(request_id="14269_C", message=self.new_request_14269_C_str)
        new_request_msg.in_progress()
        update_sample_msg = SMILEMessage.objects.create(
            request_id="14269_C_1", message=self.update_sample_14269_C_1_str
        )
        new_request(new_request_msg.id)
        tumor_or_normal = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: "14269_C_1"},
            values_metadata=settings.TUMOR_OR_NORMAL_METADATA_KEY,
        ).first()
        self.assertEqual(tumor_or_normal, "Normal")
        update_sample_job(update_sample_msg.id)
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
            self.assertEqual(ddiff["values_changed"]["root['tumorOrNormal']"]["new_value"], "Tumor")
            self.assertEqual(ddiff["values_changed"]["root['tumorOrNormal']"]["old_value"], "Normal")

        update_sample_msg.refresh_from_db()
        self.assertEqual(update_sample_msg.status, SmileMessageStatus.COMPLETED)
        print(update_sample_msg.sample_status)

    @patch("os.access")
    @patch("notifier.tasks.notifier_start")
    @patch("notifier.tasks.send_notification.delay")
    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("os.path.exists")
    @patch("beagle_etl.jobs.helper_jobs.calculate_checksum.delay")
    @override_settings(IMPORT_FILE_GROUP="1a1b29cf-3bc2-4f6c-b376-d4c5d701166a")
    def test_update_sample_new_fastqs(
        self,
        calculate_checksum,
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
        calculate_checksum.return_value = None
        populate_job_group.return_value = None
        send_notification.return_value = None
        job_group_notifier_get.return_value = self.job_group_notifier
        notifier_start.return_value = True
        send_notification.return_value = True
        access.return_value = os.R_OK
        settings.NOTIFIER_ACTIVE = False
        path_exists.return_value = True

        new_request_msg = SMILEMessage.objects.create(request_id="14269_C", message=self.new_request_14269_C_str)
        new_request_msg.in_progress()
        update_sample_msg = SMILEMessage.objects.create(
            request_id="14269_C_1", message=self.update_sample_14269_C_1_new_files_str
        )
        update_sample_msg.in_progress()
        new_request(new_request_msg.id)
        tumor_or_normal = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: "14269_C_1"},
            values_metadata=settings.TUMOR_OR_NORMAL_METADATA_KEY,
        ).first()
        self.assertEqual(tumor_or_normal, "Normal")
        update_sample_job(update_sample_msg.id)
        tumor_or_normal = FileRepository.filter(
            metadata={settings.SAMPLE_ID_METADATA_KEY: "14269_C_1"},
            values_metadata=settings.TUMOR_OR_NORMAL_METADATA_KEY,
        ).first()
        self.assertEqual(tumor_or_normal, "Tumor")

        files = FileRepository.filter(metadata={settings.SAMPLE_ID_METADATA_KEY: "14269_C_1"})
        self.assertEqual(len(files), 2)

        for file in files:
            self.assertTrue(file.file.path.endswith("new.fastq.gz"))

        update_sample_msg.refresh_from_db()
        self.assertEqual(update_sample_msg.status, SmileMessageStatus.COMPLETED)
        print(update_sample_msg.sample_status)

    @patch("os.access")
    @patch("notifier.tasks.notifier_start")
    @patch("notifier.tasks.send_notification.delay")
    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("os.path.exists")
    @patch("beagle_etl.jobs.helper_jobs.calculate_checksum.delay")
    @override_settings(IMPORT_FILE_GROUP="1a1b29cf-3bc2-4f6c-b376-d4c5d701166a")
    def test_update_sample_update(
        self,
        calculate_checksum,
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
        calculate_checksum.return_value = None

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
        update_sample_job(str(msg.id))

        msg.refresh_from_db()
        self.assertEqual(msg.status, SmileMessageStatus.COMPLETED)
