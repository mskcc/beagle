from unittest.mock import patch
from django.test import TestCase
from file_system.models import File, FileGroup, FileType, Storage, StorageType
from file_manager.models import FileProviderJob, SampleProviderJob
from file_manager.file_manager.file_manager import FileManager


class StageFileTest(TestCase):
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
        self.sample_job = SampleProviderJob.objects.create(sample_id="Sample_001")

    @patch("file_manager.file_manager.file_manager.CopyService.remap")
    def test_stage_file_links_sample_job(self, mock_remap):
        """stage_file persists the sample job on the FileProviderJob it creates"""
        mock_remap.return_value = "/staged/path/test.fastq"

        file_manager = FileManager(file_group=self.file_group)
        file_manager.stage_file(self.file, gene_panel=None, sample_job=str(self.sample_job.id))

        job = FileProviderJob.objects.get(file_object=self.file)
        self.assertEqual(job.sample_job, self.sample_job)
