import uuid
from enum import IntEnum
from django.db import models
from django.db import transaction
from django.db.models import F
from file_system.models import File


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_date = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_date = models.DateTimeField(auto_now=True)


class FileProviderStatus(IntEnum):
    SCHEDULED = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3


class SampleProviderJobManager(models.Manager):
    def get_or_create_for_sample(self, sample_id):
        return self.get_or_create(sample_id=sample_id, defaults={"status": FileProviderStatus.SCHEDULED})

    def is_sample_completed(self, sample_id):
        try:
            job = self.get(sample_id=sample_id)
            return job.is_completed()
        except SampleProviderJob.DoesNotExist:
            return False


class SampleProviderJob(BaseModel):
    sample_id = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in FileProviderStatus],
        default=FileProviderStatus.SCHEDULED,
        db_index=True,
    )
    total_files = models.IntegerField(default=0)
    completed_files = models.IntegerField(default=0)

    objects = SampleProviderJobManager()

    def is_completed(self):
        """Check if all files for this request are completed."""
        return self.total_files > 0 and self.completed_files >= self.total_files

    def increment_completed(self):
        """Increment completed files count and update status if all done (thread-safe)."""
        with transaction.atomic():
            job = SampleProviderJob.objects.select_for_update().get(id=self.id)
            SampleProviderJob.objects.filter(id=self.id).update(completed_files=F("completed_files") + 1)
            job.refresh_from_db()

            if job.is_completed():
                job.status = FileProviderStatus.COMPLETED
            else:
                job.status = FileProviderStatus.IN_PROGRESS
            job.save()


class FileProviderManager(models.Manager):
    def provide_file(self, file_object, original_path, staged_path):
        """
        Create a FileProviderJob for the given file, preventing duplicates.
        Returns (job, created) tuple.
        """
        with transaction.atomic():
            # select_for_update locks the matching rows
            existing = (
                FileProviderJob.objects.select_for_update()
                .filter(
                    file_object=file_object,
                    original_path=original_path,
                    staged_path=staged_path,
                    status__in=(FileProviderStatus.SCHEDULED, FileProviderStatus.IN_PROGRESS),
                )
                .first()
            )

            if existing:
                return existing, False

            job = FileProviderJob.objects.create(
                file_object=file_object,
                original_path=original_path,
                staged_path=staged_path,
            )
            return job, True


class FileProviderJob(BaseModel):
    file_object = models.ForeignKey(File, null=True, on_delete=models.CASCADE)
    original_path = models.CharField(max_length=1500, db_index=True)
    staged_path = models.CharField(max_length=1500, db_index=True)
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in FileProviderStatus],
        default=FileProviderStatus.SCHEDULED,
        db_index=True,
    )

    class Meta:
        constraints = [models.UniqueConstraint(fields=["file_object"], name="unique_file_provider_job_per_file")]

    def in_progress(self):
        self.status = FileProviderStatus.IN_PROGRESS
        self.save()

    def set_completed(self):
        self.status = FileProviderStatus.COMPLETED
        self.save()

    def set_failed(self):
        self.status = FileProviderStatus.FAILED
        self.save()

    objects = FileProviderManager()


class CleanupFileJob(BaseModel):
    file_object = models.ForeignKey(File, null=True, on_delete=models.CASCADE)
    original_path = models.CharField(max_length=1500, db_index=True)
    status = models.IntegerField(
        choices=[(status.value, status.name) for status in FileProviderStatus],
        default=FileProviderStatus.SCHEDULED,
        db_index=True,
    )
    cleanup_date = models.DateField(db_index=True)

    def set_completed(self):
        self.status = FileProviderStatus.COMPLETED
        self.save()
