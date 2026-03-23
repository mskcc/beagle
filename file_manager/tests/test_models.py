import uuid
from django.test import TestCase
from file_system.models import File, FileGroup, FileType, Storage, StorageType
from file_manager.models import (
    FileProviderStatus,
    FileProviderJob,
    SampleProviderJob,
    CleanupFileJob,
)
from datetime import date, timedelta


class SampleProviderJobTest(TestCase):
    def setUp(self):
        self.sample_id = "Sample_001"

    def test_create_sample_provider_job(self):
        job = SampleProviderJob.objects.create(sample_id=self.sample_id, total_files=5, completed_files=0)
        self.assertEqual(job.sample_id, self.sample_id)
        self.assertEqual(job.total_files, 5)
        self.assertEqual(job.completed_files, 0)
        self.assertEqual(job.status, FileProviderStatus.SCHEDULED)

    def test_is_completed_false(self):
        job = SampleProviderJob.objects.create(sample_id=self.sample_id, total_files=5, completed_files=3)
        self.assertFalse(job.is_completed())

    def test_is_completed_true(self):
        job = SampleProviderJob.objects.create(sample_id=self.sample_id, total_files=5, completed_files=5)
        self.assertTrue(job.is_completed())

    def test_increment_completed(self):
        job = SampleProviderJob.objects.create(sample_id=self.sample_id, total_files=3, completed_files=0)

        job.increment_completed()
        job.refresh_from_db()
        self.assertEqual(job.completed_files, 1)
        self.assertEqual(job.status, FileProviderStatus.IN_PROGRESS)

        job.increment_completed()
        job.refresh_from_db()
        self.assertEqual(job.completed_files, 2)
        self.assertEqual(job.status, FileProviderStatus.IN_PROGRESS)

        job.increment_completed()
        job.refresh_from_db()
        self.assertEqual(job.completed_files, 3)
        self.assertEqual(job.status, FileProviderStatus.COMPLETED)


class FileProviderJobTest(TestCase):
    def setUp(self):
        self.storage = Storage.objects.create(name="test_storage", type=StorageType.LOCAL)
        self.file_group = FileGroup.objects.create(name="test_group", storage=self.storage)
        self.file_type = FileType.objects.create(name="fastq")
        self.file = File.objects.create(
            file_name="test.fastq",
            path="/original/path/test.fastq",
            file_type=self.file_type,
            file_group=self.file_group,
        )

    def test_create_file_provider_job(self):
        job = FileProviderJob.objects.create(
            file_object=self.file,
            original_path="/original/path/test.fastq",
            staged_path="/staged/path/test.fastq",
        )
        self.assertEqual(job.file_object, self.file)
        self.assertEqual(job.original_path, "/original/path/test.fastq")
        self.assertEqual(job.staged_path, "/staged/path/test.fastq")
        self.assertEqual(job.status, FileProviderStatus.SCHEDULED)

    def test_in_progress(self):
        job = FileProviderJob.objects.create(
            file_object=self.file,
            original_path="/original/path/test.fastq",
            staged_path="/staged/path/test.fastq",
        )
        job.in_progress()
        job.refresh_from_db()
        self.assertEqual(job.status, FileProviderStatus.IN_PROGRESS)

    def test_set_completed(self):
        job = FileProviderJob.objects.create(
            file_object=self.file,
            original_path="/original/path/test.fastq",
            staged_path="/staged/path/test.fastq",
        )
        job.set_completed()
        job.refresh_from_db()
        self.assertEqual(job.status, FileProviderStatus.COMPLETED)

    def test_unique_constraint_per_file(self):
        """Test that only one active FileProviderJob can exist per File"""
        FileProviderJob.objects.create(
            file_object=self.file,
            original_path="/original/path/test.fastq",
            staged_path="/staged/path/test.fastq",
        )

        # Creating another job for the same file should raise an IntegrityError
        with self.assertRaises(Exception):
            FileProviderJob.objects.create(
                file_object=self.file,
                original_path="/original/path/test.fastq",
                staged_path="/staged/path2/test.fastq",
            )


class CleanupFileJobTest(TestCase):
    def setUp(self):
        self.storage = Storage.objects.create(name="test_storage", type=StorageType.LOCAL)
        self.file_group = FileGroup.objects.create(name="test_group", storage=self.storage)
        self.file_type = FileType.objects.create(name="fastq")
        self.file = File.objects.create(
            file_name="test.fastq",
            path="/staged/path/test.fastq",
            file_type=self.file_type,
            file_group=self.file_group,
        )

    def test_create_cleanup_file_job(self):
        cleanup_date = date.today() + timedelta(days=30)
        job = CleanupFileJob.objects.create(
            file_object=self.file,
            original_path="/original/path/test.fastq",
            cleanup_date=cleanup_date,
        )
        self.assertEqual(job.file_object, self.file)
        self.assertEqual(job.original_path, "/original/path/test.fastq")
        self.assertEqual(job.cleanup_date, cleanup_date)
        self.assertEqual(job.status, FileProviderStatus.SCHEDULED)

    def test_set_completed(self):
        cleanup_date = date.today() + timedelta(days=30)
        job = CleanupFileJob.objects.create(
            file_object=self.file,
            original_path="/original/path/test.fastq",
            cleanup_date=cleanup_date,
        )
        job.set_completed()
        job.refresh_from_db()
        self.assertEqual(job.status, FileProviderStatus.COMPLETED)

    def test_filter_by_cleanup_date(self):
        """Test that we can query cleanup jobs by date"""
        today = date.today()
        future_date = today + timedelta(days=30)

        # Create job for today
        job_today = CleanupFileJob.objects.create(
            file_object=self.file,
            original_path="/original/path/test.fastq",
            cleanup_date=today,
        )

        # Create job for future
        file2 = File.objects.create(
            file_name="test2.fastq",
            path="/staged/path/test2.fastq",
            file_type=self.file_type,
            file_group=self.file_group,
        )
        job_future = CleanupFileJob.objects.create(
            file_object=file2,
            original_path="/original/path/test2.fastq",
            cleanup_date=future_date,
        )

        # Query for today's jobs
        today_jobs = CleanupFileJob.objects.filter(cleanup_date=today)
        self.assertEqual(today_jobs.count(), 1)
        self.assertEqual(today_jobs.first().id, job_today.id)
