import os
from django.utils import timezone
from .models import FileProviderStatus, SampleProviderJob


ACTIVE_SAMPLE_STATUSES = (FileProviderStatus.SCHEDULED, FileProviderStatus.IN_PROGRESS)


def _basename(path):
    return os.path.basename(path) if path else path


def _bucket_files(file_jobs):
    """Group a sample's file jobs into status buckets for the dashboard."""
    scheduled, copying, failed = [], [], []
    done_count = 0
    for fj in file_jobs:
        if fj.status == FileProviderStatus.SCHEDULED:
            scheduled.append(_basename(fj.staged_path))
        elif fj.status == FileProviderStatus.IN_PROGRESS:
            copying.append(_basename(fj.staged_path))
        elif fj.status == FileProviderStatus.COMPLETED:
            done_count += 1
        elif fj.status == FileProviderStatus.FAILED:
            failed.append(_basename(fj.staged_path))
    return {
        "scheduled": scheduled,
        "copying": copying,
        "done_count": done_count,
        "failed": failed,
    }


def build_dashboard_payload():
    """Build the live staging dashboard payload: active samples with files bucketed by status."""
    samples = (
        SampleProviderJob.objects.filter(status__in=ACTIVE_SAMPLE_STATUSES)
        .prefetch_related("file_jobs")
        .order_by("created_date")
    )

    sample_data = []
    for sample in samples:
        sample_data.append(
            {
                "sample_id": sample.sample_id,
                "status": FileProviderStatus(sample.status).name,
                "completed": sample.completed_files,
                "total": sample.total_files,
                "files": _bucket_files(sample.file_jobs.all()),
            }
        )

    return {
        "samples": sample_data,
        "generated_at": timezone.now().isoformat(),
    }
