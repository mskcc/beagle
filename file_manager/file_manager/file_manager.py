from django.conf import settings
from file_system.repository import FileRepository
from file_manager.copy_service import CopyService
from file_manager.tasks import stage_file_job
from file_manager.models import FileProviderStatus, FileProviderJob, CleanupFileJob, SampleProviderJob


class FileManager(object):

    def __init__(self, file_group=settings.IMPORT_FILE_GROUP):
        self.file_group = file_group

    def stage_sample(self, sample_id):
        sample_job, created = SampleProviderJob.objects.get_or_create_for_sample(sample_id)

        files = FileRepository.filter(metadata={settings.SAMPLE_ID_METADATA_KEY, sample_id},
                                      file_group=self.file_group)
        gene_panel = FileRepository.filter(metadata={settings.SAMPLE_ID_METADATA_KEY, sample_id},
                                           file_group=self.file_group,
                                           values_metadata=settings.RECIPE_METADATA_KEY).first()

        files_to_stage = 0
        for f in files:
            if not f.file.is_available:
                new_path = CopyService.remap(gene_panel, f.file.path)
                if new_path != f.file.path:
                    files_to_stage += 1

        sample_job.total_files = files_to_stage
        sample_job.save()

        for f in files:
            self.stage_file(f.file, gene_panel, sample_id)

        return sample_job


    def stage_file(self, file_obj, gene_panel, sample_job=None):
        if not file_obj.is_available:
            new_path = CopyService.remap(gene_panel, file_obj.path)
            if new_path != file_obj.path:
                fp_job, created = FileProviderJob.objects.provide_file(file_obj, file_obj.path, new_path)
                if created:
                    stage_file_job.delay(fp_job.id, sample_job)