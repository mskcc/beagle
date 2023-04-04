"""
Tests for METADB ETL jobs
"""

import os
from mock import patch
import json
from django.test import TestCase
from django.conf import settings
from django.contrib.auth.models import User
from beagle_etl.models import SMILEMessage
from beagle_etl.jobs.metadb_jobs import update_request_job, update_sample_job
from django.core.management import call_command
from file_system.repository import FileRepository


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
        self.etl_user = User.objects.create_superuser("ETL", "voyager-etl@mskcc.org", "password")

    @patch("notifier.models.JobGroupNotifier.objects.get")
    @patch("notifier.tasks.send_notification.delay")
    @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    @patch("beagle_etl.jobs.metadb_jobs.create_request_callback_instance")
    def test_update_request_metadata(
        self, request_callback, populate_job_group, send_notification, jobGroupNotifierObjectGet
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
            request_callback.return_value = None
            populate_job_group.return_value = None
            jobGroupNotifierObjectGet.return_value = None
            send_notification.return_value = None
            msg = SMILEMessage.objects.create(topic="update_request", message=self.update_request_str)
            update_request_job(str(msg.id))
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
    @patch("beagle_etl.jobs.metadb_jobs._generate_ticket_description")
    def test_update_request_ticket(
        self, ticket_description, request_callback, populate_job_group, send_notification, jobGroupNotifierObjectGet
    ):
        """
        Test that generate ticket is called properly in update request
        """
        with self.settings(ETL_USER=str(self.etl_user.username)):
            request_callback.return_value = None
            populate_job_group.return_value = None
            jobGroupNotifierObjectGet.return_value = None
            send_notification.return_value = None
            msg = SMILEMessage.objects.create(topic="update_request", message=self.update_request_str)
            update_request_job(str(msg.id))
            files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "10075_D_2"})
            sample_names = []
            for file in files:
                sample_name = file.metadata[settings.SAMPLE_ID_METADATA_KEY]
                if sample_name not in sample_names:
                    sample_names.append(sample_name)
            ticket_description.assert_called_once()
            call_args = ticket_description.call_args[0]
            self.assertEqual(call_args[0], "10075_D_2")
            self.assertEqual(len(call_args[3]), len(sample_names))
            request_metadata = call_args[5]
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
            sample_metadata = {}
            msg = SMILEMessage.objects.create(topic="update_sample", message=self.new_sample_data_str)
            update_sample_job(str(msg.id))
            sample_files = FileRepository.filter(metadata={settings.SAMPLE_ID_METADATA_KEY: "10075_D_2_3"})
            for f in sample_files:
                self.assertEqual(f.metadata["sampleName"], "XXX002_P3_12345_L1")

    # @patch("notifier.models.JobGroupNotifier.objects.get")
    # @patch("notifier.tasks.send_notification.delay")
    # @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    # def test_update_sample_new(self, populate_job_group, send_notification, jobGroupNotifierObjectGet):
    #     """
    #     Test that new samples are properly added
    #     """
    #     populate_job_group.return_value = None
    #     jobGroupNotifierObjectGet.return_value = None
    #     send_notification.return_value = None
    #     sample_metadata = {}
    #     for single_sample in self.new_request_data["samples"]:
    #         sample_name = single_sample[settings.SAMPLE_ID_METADATA_KEY]
    #         if sample_name not in sample_metadata:
    #             sample_metadata[sample_name] = single_sample
    #     update_sample_job(self.request_data_str)
    #     files = FileRepository.filter(metadata={settings.REQUEST_ID_METADATA_KEY: "10075_D_2"})
    #     self.assertEqual(len(files), 10)
    #     for file in files:
    #         metadata_keys = file.metadata.keys()
    #         sample_name = file.metadata[settings.SAMPLE_ID_METADATA_KEY]
    #         for single_metadata_key in metadata_keys:
    #             if single_metadata_key in sample_metadata:
    #                 if single_metadata_key in self.file_keys:
    #                     continue
    #                 current_value = file.metadata[single_metadata_key]
    #                 expected_value = sample_metadata[sample_name][single_metadata_key]
    #                 self.assertEqual(current_value, expected_value)

    # @patch("notifier.models.JobGroupNotifier.objects.get")
    # @patch("notifier.tasks.send_notification.delay")
    # @patch("file_system.tasks.populate_job_group_notifier_metadata.delay")
    # def test_update_sample_update(self, populate_job_group, send_notification, jobGroupNotifierObjectGet):
    #     """
    #     Test that samples metadata is properly updated
    #     """
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
