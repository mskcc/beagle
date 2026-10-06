import logging
from datetime import datetime

from runner.models import Pipeline
from runner.operator.operator import Operator
from runner.run.objects.run_creator_object import RunCreator
from file_system.repository.file_repository import FileRepository

LOGGER = logging.getLogger(__name__)

# "dmp-bams" file group -- same DMP clinical bam metadata + files that ACCESS
# Data Analysis's clinical rows pull from (see DMP_BAM_FILE_GROUP in
# runner/operator/access/data_analysis/data_analysis.py). There is no separate
# "XS clinical" file group; clinical ACCESS (as opposed to IMPACT) is just
# this group filtered to metadata.assay in ("XS1", "XS2").
DMP_BAM_FILE_GROUP = "d4775633-f53f-412f-afa5-46e9a86b654b"
CLINICAL_ACCESS_ASSAYS = ("XS1", "XS2")
STANDARD_BAM_SUFFIX = "-standard.bam"

SAMPLESHEET_COLUMNS = ["sample_id", "tumor_bam", "normal_bam", "matched_norm_sample_barcode"]


def _create_file_object(path):
    """CWL File object; the nextflow template processor renders this to a path in the samplesheet CSV."""
    return {"class": "File", "location": "iris://" + path}


class StrideOperator(Operator):
    """
    Operator for the STRiDE (MSI prediction) nextflow pipeline
    (https://github.com/msk-access/STRiDE). Builds the samplesheet described
    by examples/samples_cluster_cohort10.csv:

        sample_id, tumor_bam, normal_bam, matched_norm_sample_barcode

    Unlike most operators, this one runs against an explicit list of tumor
    sample ids rather than an IGO request id -- STRiDE is run ad hoc against
    a chosen cohort, not per-request. Each sample id is the DMP clinical
    ACCESS `sample` value (e.g. "P-0109895-T03-XS2"), looked up in the
    "dmp-bams" file group.

    Each tumor is paired with its matched normal from the same patient/batch
    -- same metadata.project_name + metadata.patient.cmo + metadata.patient.dmp
    + metadata.assay, type Normal -- picking the first such match. Only the
    standard bam is used for either side of the pair (STRiDE runs on standard
    ACCESS bams, not duplex/simplex/unfilter).
    """

    def get_jobs(self, sample_ids=None):
        if not sample_ids:
            raise Exception(
                "STRiDE: no sample_ids given; this operator requires an explicit list of tumor sample ids"
            )

        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")

        rows = [row for row in (self._build_row(sample_id) for sample_id in sample_ids) if row]
        if not rows:
            raise Exception("STRiDE: no samplesheet rows could be built for sample_ids {}".format(sample_ids))

        job_json = {
            "name": "STRiDE: {} sample(s), {}".format(len(rows), run_date),
            "app": app,
            "inputs": {"input": rows},
            "tags": {
                "pipeline": pipeline.name,
                "pipeline_version": pipeline.version,
                "sample_ids": sample_ids,
            },
            "output_metadata": {},
        }
        return [RunCreator(**job_json)]

    def _build_row(self, sample_id):
        tumor_meta, tumor_bam = self._clinical_standard_bam(metadata__sample=sample_id)
        if not tumor_meta:
            LOGGER.warning("STRiDE: no clinical ACCESS sample found for %s; skipping", sample_id)
            return None
        if (tumor_meta.get("type") or "").upper() != "T":
            LOGGER.warning("STRiDE: sample %s is not a tumor (type=%r); skipping", sample_id, tumor_meta.get("type"))
            return None
        if not tumor_bam:
            LOGGER.warning("STRiDE: tumor sample %s has no standard bam; skipping", sample_id)
            return None

        patient = tumor_meta.get("patient") or {}
        normal_meta, normal_bam = self._clinical_standard_bam(
            metadata__project_name=tumor_meta.get("project_name"),
            metadata__patient__cmo=patient.get("cmo"),
            metadata__patient__dmp=patient.get("dmp"),
            metadata__assay=tumor_meta.get("assay"),
            metadata__type="N",
        )
        if not normal_meta or not normal_bam:
            LOGGER.warning(
                "STRiDE: no matched normal standard bam for tumor %s (project_name=%r, patient.cmo=%r, "
                "patient.dmp=%r, assay=%r); skipping",
                sample_id,
                tumor_meta.get("project_name"),
                patient.get("cmo"),
                patient.get("dmp"),
                tumor_meta.get("assay"),
            )
            return None

        return {
            "sample_id": sample_id,
            "tumor_bam": _create_file_object(tumor_bam),
            "normal_bam": _create_file_object(normal_bam),
            "matched_norm_sample_barcode": normal_meta.get("sample") or "",
        }

    @staticmethod
    def _clinical_standard_bam(**metadata_filters):
        """
        First (metadata, standard_bam_path) match in the DMP bams file group for
        the given metadata filters, restricted to clinical ACCESS (XS1/XS2) and
        to the standard bam file. Every bam file for one DMP sample shares the
        same metadata, so filtering straight to the standard bam's row gives
        both the metadata and its path in one query. Returns (None, None) if
        nothing matches.
        """
        fm = (
            FileRepository.filter(file_group=DMP_BAM_FILE_GROUP)
            .filter(
                file__file_name__iendswith=STANDARD_BAM_SUFFIX,
                metadata__assay__in=CLINICAL_ACCESS_ASSAYS,
                **metadata_filters,
            )
            .exclude(metadata__active=False)
            .order_by("file__file_name")
            .first()
        )
        if not fm:
            return None, None
        return fm.metadata or {}, fm.file.path
