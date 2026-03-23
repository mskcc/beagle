import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.conf import settings
from datetime import date, timedelta
from file_system.models import File, FileGroup, FileType, Storage, StorageType
from file_manager.models import (
    FileProviderStatus,
    FileProviderJob,
    SampleProviderJob,
    CleanupFileJob,
)
from file_manager.tasks import stage_file_job, check_for_clean_up, clean_up_file


class StageFileJobTest(TestCase):
    def setUp(self):
        self.storage = Storage.objects.create(name="test_storage", type=StorageType.LOCAL)
        self.file_group = FileGroup.objects.create(name="test_group", storage=self.storage)
        self.file_type = FileType.objects.create(name="fastq")
        self.file = File.objects.create(
            file_name="test.fastq",
            path="/original/path/test.fastq",
            file_type=self.file_type,
            file_group=self.file_group,
            available=False,
        )
        self.sample_job = SampleProviderJob.objects.create(sample_id="Sample_001", total_files=1, completed_files=0)
        self.file_provider_job = FileProviderJob.objects.create(
            file_object=self.file,
            original_path="/original/path/test.fastq",
            staged_path="/staged/path/test.fastq",
        )

    @override_settings(STAGE_DAYS=30)
    @patch("file_manager.tasks.CopyService.copy")
    def test_stage_file_job_success(self, mock_copy):
        """Test successful file staging"""
        stage_file_job(str(self.file_provider_job.id), str(self.sample_job.id))

        # Verify copy was called
        mock_copy.assert_called_once_with("/original/path/test.fastq", "/staged/path/test.fastq")

        # Verify job status updated
        self.file_provider_job.refresh_from_db()
        self.assertEqual(self.file_provider_job.status, FileProviderStatus.COMPLETED)

        # Verify file updated
        self.file.refresh_from_db()
        self.assertEqual(self.file.path, "/staged/path/test.fastq")
        self.assertTrue(self.file.is_available)

        # Verify sample job progress
        self.sample_job.refresh_from_db()
        self.assertEqual(self.sample_job.completed_files, 1)

        # Verify cleanup job created
        cleanup_jobs = CleanupFileJob.objects.filter(file_object=self.file)
        self.assertEqual(cleanup_jobs.count(), 1)
        cleanup_job = cleanup_jobs.first()
        expected_cleanup_date = date.today() + timedelta(days=30)
        self.assertEqual(cleanup_job.cleanup_date, expected_cleanup_date)
        self.assertEqual(cleanup_job.original_path, "/original/path/test.fastq")

    @override_settings(STAGE_DAYS=30)
    @patch("file_manager.tasks.CopyService.copy")
    def test_stage_file_job_without_sample_job(self, mock_copy):
        """Test staging without a sample job"""
        stage_file_job(str(self.file_provider_job.id), None)

        # Verify copy was still called
        mock_copy.assert_called_once()

        # Verify job status updated
        self.file_provider_job.refresh_from_db()
        self.assertEqual(self.file_provider_job.status, FileProviderStatus.COMPLETED)

        # Sample job should remain unchanged
        self.sample_job.refresh_from_db()
        self.assertEqual(self.sample_job.completed_files, 0)

    @override_settings(STAGE_DAYS=7)
    @patch("file_manager.tasks.CopyService.copy")
    def test_stage_file_job_custom_stage_days(self, mock_copy):
        """Test that STAGE_DAYS setting is respected"""
        stage_file_job(str(self.file_provider_job.id))

        # Verify cleanup job has correct date
        cleanup_job = CleanupFileJob.objects.get(file_object=self.file)
        expected_cleanup_date = date.today() + timedelta(days=7)
        self.assertEqual(cleanup_job.cleanup_date, expected_cleanup_date)


class CheckForCleanUpTest(TestCase):
    def setUp(self):
        self.storage = Storage.objects.create(name="test_storage", type=StorageType.LOCAL)
        self.file_group = FileGroup.objects.create(name="test_group", storage=self.storage)
        self.file_type = FileType.objects.create(name="fastq")
        self.file1 = File.objects.create(
            file_name="test1.fastq",
            path="/staged/path/test1.fastq",
            file_type=self.file_type,
            file_group=self.file_group,
        )
        self.file2 = File.objects.create(
            file_name="test2.fastq",
            path="/staged/path/test2.fastq",
            file_type=self.file_type,
            file_group=self.file_group,
        )

    @patch("file_manager.tasks.clean_up_file.delay")
    def test_check_for_clean_up_finds_jobs(self, mock_cleanup):
        """Test that check_for_clean_up finds jobs due today"""
        today = date.today()

        # Create cleanup job for today
        job_today = CleanupFileJob.objects.create(
            file_object=self.file1,
            original_path="/original/path/test1.fastq",
            cleanup_date=today,
        )

        # Create cleanup job for future
        job_future = CleanupFileJob.objects.create(
            file_object=self.file2,
            original_path="/original/path/test2.fastq",
            cleanup_date=today + timedelta(days=5),
        )

        check_for_clean_up()

        # Verify only today's job was queued
        mock_cleanup.assert_called_once_with(str(job_today.id))

    @patch("file_manager.tasks.clean_up_file.delay")
    def test_check_for_clean_up_no_jobs(self, mock_cleanup):
        """Test that check_for_clean_up handles no jobs gracefully"""
        # Create only future jobs
        CleanupFileJob.objects.create(
            file_object=self.file1,
            original_path="/original/path/test1.fastq",
            cleanup_date=date.today() + timedelta(days=10),
        )

        check_for_clean_up()

        # Verify no cleanup tasks were queued
        mock_cleanup.assert_not_called()


class CleanUpFileTest(TestCase):
    def setUp(self):
        self.storage = Storage.objects.create(name="test_storage", type=StorageType.LOCAL)
        self.file_group = FileGroup.objects.create(name="test_group", storage=self.storage)
        self.file_type = FileType.objects.create(name="fastq")
        self.file = File.objects.create(
            file_name="test.fastq",
            path="/staged/path/test.fastq",
            file_type=self.file_type,
            file_group=self.file_group,
            available=True,
        )
        self.cleanup_job = CleanupFileJob.objects.create(
            file_object=self.file,
            original_path="/original/path/test.fastq",
            cleanup_date=date.today(),
        )

    def test_clean_up_file_success(self):
        """Test successful file cleanup"""
        # Create a real temporary file to test deletion
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b"test content")

        # Update file to point to temp file
        self.file.path = tmp_path
        self.file.save()

        clean_up_file(str(self.cleanup_job.id))

        # Verify file was deleted
        self.assertFalse(os.path.exists(tmp_path))

        # Verify file object updated
        self.file.refresh_from_db()
        self.assertEqual(self.file.path, "/original/path/test.fastq")
        self.assertFalse(self.file.is_available)

        # Verify cleanup job marked complete
        self.cleanup_job.refresh_from_db()
        self.assertEqual(self.cleanup_job.status, FileProviderStatus.COMPLETED)

    def test_clean_up_file_not_exists(self):
        """Test cleanup when file doesn't exist"""
        # Set path to non-existent file
        self.file.path = "/non/existent/file.fastq"
        self.file.save()

        clean_up_file(str(self.cleanup_job.id))

        # Should still update the database records
        self.file.refresh_from_db()
        self.assertEqual(self.file.path, "/original/path/test.fastq")
        self.assertFalse(self.file.is_available)

        self.cleanup_job.refresh_from_db()
        self.assertEqual(self.cleanup_job.status, FileProviderStatus.COMPLETED)

    @patch("file_manager.tasks.os.remove")
    @patch("file_manager.tasks.os.path.exists")
    def test_clean_up_file_deletion_error(self, mock_exists, mock_remove):
        """Test cleanup handles deletion errors gracefully"""
        mock_exists.return_value = True
        mock_remove.side_effect = PermissionError("Permission denied")

        clean_up_file(str(self.cleanup_job.id))

        # Verify file was attempted to be deleted
        mock_remove.assert_called_once()

        # Verify cleanup job NOT marked complete due to error
        self.cleanup_job.refresh_from_db()
        self.assertEqual(self.cleanup_job.status, FileProviderStatus.SCHEDULED)

        # File should not be updated either
        self.file.refresh_from_db()
        self.assertEqual(self.file.path, "/staged/path/test.fastq")
        self.assertTrue(self.file.is_available)

    def test_clean_up_file_job_not_found(self):
        """Test cleanup with non-existent job ID"""
        fake_id = "00000000-0000-0000-0000-000000000000"

        # Should not raise exception
        clean_up_file(fake_id)

        # Original job should be unchanged
        self.cleanup_job.refresh_from_db()
        self.assertEqual(self.cleanup_job.status, FileProviderStatus.SCHEDULED)
