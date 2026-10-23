from file_system.repository.file_repository import FileRepository
from runner.models import Run, RunStatus

# "dmp-bams" file group -- same DMP clinical bam metadata + files used by
# AccessV2DataAnalysisOperator's clinical rows and StrideOperator.
DMP_BAM_FILE_GROUP = "d4775633-f53f-412f-afa5-46e9a86b654b"
CLINICAL_ACCESS_ASSAYS = ("XS1", "XS2")
STANDARD_BAM_SUFFIX = "-standard.bam"
# A sample with a Run in one of these states for the pipeline counts as already
# submitted. FAILED/TERMINATED are left out so they get picked up again.
SUBMITTED_RUN_STATUSES = (RunStatus.CREATING, RunStatus.READY, RunStatus.RUNNING, RunStatus.COMPLETED)


def find_all_clinical_access_tumor_sample_ids():
    """
    Every active clinical ACCESS (XS1/XS2) tumor sample id (metadata.sample)
    in the "dmp-bams" file group that has a standard bam. Pipeline-agnostic --
    just the pool of DMP XS samples available to submit through any operator
    whose get_jobs accepts sample_ids=[...] (e.g. StrideOperator).
    """
    sample_ids = (
        FileRepository.filter(file_group=DMP_BAM_FILE_GROUP)
        .filter(
            file__file_name__iendswith=STANDARD_BAM_SUFFIX,
            metadata__assay__in=CLINICAL_ACCESS_ASSAYS,
            metadata__type="T",
        )
        .exclude(metadata__active=False)
        .values_list("metadata__sample", flat=True)
        .distinct()
    )
    return sorted({sample_id for sample_id in sample_ids if sample_id})


def find_submitted_sample_ids(sample_ids, pipeline):
    """
    The subset of sample_ids that already have a Run for this pipeline (exact
    version) that isn't FAILED/TERMINATED. Checks both Run.samples (filled in
    from the run's registered input files) and the run's tags["sample_ids"].
    The tag is what catches STRiDE: its bams go in through a rendered
    samplesheet rather than as File inputs, and DMP bam files key the sample
    under metadata["sample"] rather than primaryId, so Run.samples stays empty.
    """
    sample_ids = set(sample_ids)
    runs = Run.objects.filter(app=pipeline, status__in=SUBMITTED_RUN_STATUSES)
    submitted = set(
        runs.filter(samples__sample_id__in=sample_ids).values_list("samples__sample_id", flat=True).distinct()
    )
    for tagged_ids in runs.filter(tags__has_key="sample_ids").values_list("tags__sample_ids", flat=True):
        if isinstance(tagged_ids, list):
            submitted.update(sample_ids.intersection(tagged_ids))
    return submitted
