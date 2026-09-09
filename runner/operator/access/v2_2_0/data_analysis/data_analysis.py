import os
import logging
from collections import defaultdict
from datetime import datetime

from django.conf import settings

from runner.models import Pipeline, Port, PortType
from runner.operator.operator import Operator
from runner.operator.access import get_request_id_runs
from runner.run.objects.run_creator_object import RunCreator
from file_system.repository.file_repository import FileRepository


WORKDIR = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger(__name__)

# ~~~ Upstream pipelines ~~~
# BAM-generation pipeline (duplex / simplex / standard bams)
NUCLEO_APP_NAMES = ["access v2 nucleo", "access nucleo"]
# Small-variant pipeline (research mutations MAF)
SNV_APP_NAMES = ["access v2 legacy SNV"]

# ~~~ Nucleo output ports ~~~
# NOTE: the nucleo port names are legacy/misleading. The nf-core "standard" bam is
# {sample}_cl_aln_srt_MD_IR_FX_BR.bam, which nucleo emits on the `uncollapsed_bam`
# port (NOT `fgbio_collapsed_bam`, which carries {sample}_..._BR__aln_srt_IR_FX.bam).
NUCLEO_DUPLEX_PORT = "fgbio_filter_consensus_reads_duplex_bam"
NUCLEO_SIMPLEX_PORT = "fgbio_postprocessing_simplex_bam"
NUCLEO_STANDARD_PORT = "uncollapsed_bam"

# accessanalysis samplesheet assay_type values
ASSAY_RESEARCH_ACCESS = "research_access"
ASSAY_CLINICAL_ACCESS = "clinical_access"
ASSAY_CLINICAL_IMPACT = "clinical_impact"

# ~~~ DMP (clinical) bams ~~~
# "dmp-bams" file group. Clinical bams + metadata live here (not in nucleo ports).
DMP_BAM_FILE_GROUP = "d4775633-f53f-412f-afa5-46e9a86b654b"
# metadata.assay: exactly "XS2" -> clinical ACCESS; IM*/IH* -> clinical IMPACT.
# (XS1 clinical ACCESS samples are intentionally excluded.)
DMP_CLINICAL_ACCESS_ASSAY = "XS2"
DMP_IMPACT_ASSAY_PREFIXES = ("IM", "IH")
# DMP bam filename suffixes (the anon_id carries the same suffix in metadata)
DMP_BAM_SUFFIXES = ("duplex", "simplex", "standard", "unfilter")

# Filename of the filtered research MAF produced by the SNV pipeline:
#   {sample_id}.<normal>.combined-variants.vep_keptrmv_taggedHotspots_fillout_filtered.maf
# The <normal> segment varies, so match on the stable suffix and take the sample id
# from the part before the first ".".
SNV_FILTERED_MAF_SUFFIX = ".combined-variants.vep_keptrmv_taggedHotspots_fillout_filtered.maf"


def _create_file_object(path):
    """
    Create a simple CWL File object from a path. The nextflow template processor
    converts these into paths when it renders the samplesheet CSV.
    """
    return {"class": "File", "location": "iris://" + path}


class AccessV2DataAnalysisOperator(Operator):
    """
    Operator for the nf-core/accessanalysis workflow:

        https://github.com/nf-core/accessanalysis  (assets/schema_input.json)

    This operator is downstream of the ACCESS nucleo and snps_and_indels (SNV)
    operators. It builds the Voyager-populated samplesheet described by
    ``assets/schema_input.json``:

        combined_id, cmo_patient_id, dmp_patient_id, sample_id, assay_type,
        tumor_normal, anon_id, duplex_bam, simplex_bam, standard_bam, maf

    Data sources for research_access samples:
      - combined_id / cmo_patient_id / dmp_patient_id / sample_id / tumor_normal
        come from the request's fastq metadata.
      - duplex_bam / simplex_bam (tumor) and standard_bam (normal) come from the
        request's nucleo run output ports.
      - maf (tumor only) comes from the request's "access v2 legacy snv" run.

    Clinical samples (clinical_access / clinical_impact) are pulled for every CMO
    patient that appears in the research set:
      - bams + metadata come from the "dmp-bams" file group
        (``DMP_BAM_FILE_GROUP``), matched by ``metadata.patient.cmo``.
      - clinical_access is restricted to DMP assay "XS2"; clinical_impact is
        assay "IM*"/"IH*".
      - clinical_access tumor -> duplex_bam + simplex_bam; clinical_access normal
        -> standard_bam ("-standard.bam"); clinical_impact (any) -> standard_bam
        (plain "{anon_id}.bam", no suffix).
      - maf on a clinical row is that patient's research MAF (if any), so the
        downstream MAF-merge step can pick it up.
    """

    def get_jobs(self):
        LOGGER.info("Operator JobGroupNotifier ID %s", self.job_group_notifier_id)
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")

        # Resolve the request and its most recent completed nucleo runs.
        # get_request_id_runs raises a bare AttributeError when nothing matches
        # (its .first() is None), so translate that into a clear message.
        try:
            nucleo_runs, self.request_id = get_request_id_runs(NUCLEO_APP_NAMES, self.run_ids, self.request_id)
        except AttributeError:
            raise Exception(
                "ACCESS Data Analysis: no completed nucleo run ({}) found for request {} / run_ids {}".format(
                    " / ".join(NUCLEO_APP_NAMES), self.request_id, self.run_ids
                )
            )

        # fastq-derived per-sample metadata, keyed by cmoSampleName
        sample_meta = self.get_research_sample_metadata()
        # nucleo bams, keyed by sample id
        nucleo_bams = self.get_nucleo_bams(nucleo_runs)
        # research MAFs, keyed by sample id (tumor samples only)
        snv_mafs = self.get_snv_mafs()
        # research MAF per CMO patient, for clinical rows. One SNV run per request,
        # so at most one filtered MAF per patient is expected.
        research_maf_by_patient = {}
        for maf_sample_id, maf_path in snv_mafs.items():
            patient = "-".join(maf_sample_id.split("-")[:2])
            existing = research_maf_by_patient.get(patient)
            if existing and existing != maf_path:
                LOGGER.warning(
                    "ACCESS Data Analysis: patient %s has multiple research MAFs; keeping %s, ignoring %s",
                    patient,
                    existing,
                    maf_path,
                )
                continue
            research_maf_by_patient[patient] = maf_path

        rows = []
        for sample_id, meta in sample_meta.items():
            bams = nucleo_bams.get(sample_id, {})
            row = {
                "combined_id": meta["combined_id"],
                "cmo_patient_id": meta["cmo_patient_id"],
                "dmp_patient_id": meta["dmp_patient_id"],
                "sample_id": sample_id,
                "assay_type": ASSAY_RESEARCH_ACCESS,
                "tumor_normal": meta["tumor_normal"],
                "anon_id": "NA",
                "duplex_bam": "",
                "simplex_bam": "",
                "standard_bam": "",
                "maf": "",
            }
            if meta["tumor_normal"] == "tumor":
                if bams.get("duplex"):
                    row["duplex_bam"] = _create_file_object(bams["duplex"])
                if bams.get("simplex"):
                    row["simplex_bam"] = _create_file_object(bams["simplex"])
                if snv_mafs.get(sample_id):
                    row["maf"] = _create_file_object(snv_mafs[sample_id])
            else:
                if bams.get("standard"):
                    row["standard_bam"] = _create_file_object(bams["standard"])
            rows.append(row)

        if not rows:
            raise Exception(
                "ACCESS Data Analysis: no research_access samples found for request {}".format(self.request_id)
            )

        # Clinical (DMP) samples for every CMO patient seen in the research set
        cmo_patient_ids = {m["cmo_patient_id"] for m in sample_meta.values() if m["cmo_patient_id"]}
        rows.extend(self.get_clinical_rows(cmo_patient_ids, research_maf_by_patient))

        input_json = {"input": rows}
        job_json = {
            "name": "ACCESS Data Analysis: {request_id}, {run_date}".format(
                request_id=self.request_id, run_date=run_date
            ),
            "app": app,
            "inputs": input_json,
            "tags": {
                settings.REQUEST_ID_METADATA_KEY: self.request_id,
                "pipeline": pipeline.name,
                "pipeline_version": pipeline.version,
            },
            "output_metadata": {},
        }
        return [RunCreator(**job_json)]

    def get_research_sample_metadata(self):
        """
        Pull per-sample metadata from the request's fastq files (same query the
        nucleo operator uses). Returns a dict keyed by cmoSampleName:

            {sample_id: {combined_id, cmo_patient_id, dmp_patient_id, tumor_normal}}
        """
        files = FileRepository.filter(
            queryset=self.files,
            metadata={
                settings.REQUEST_ID_METADATA_KEY: self.request_id,
                settings.IGO_COMPLETE_METADATA_KEY: True,
            },
            filter_redact=True,
        )

        sample_meta = {}
        for f in files:
            m = f.metadata
            sample_id = m.get(settings.CMO_SAMPLE_NAME_METADATA_KEY)
            if not sample_id or sample_id in sample_meta:
                continue

            cmo_patient_id = m.get(settings.PATIENT_ID_METADATA_KEY) or ""
            # Research samples have no DMP patient id in Voyager; leave blank so the
            # combined_id is just the CMO patient id.
            dmp_patient_id = ""
            combined_id = "_".join([p for p in [cmo_patient_id, dmp_patient_id] if p])

            tumor_normal = (m.get(settings.TUMOR_OR_NORMAL_METADATA_KEY) or "").strip().lower()
            tumor_normal = "tumor" if tumor_normal.startswith("t") else "normal"

            sample_meta[sample_id] = {
                "combined_id": combined_id,
                "cmo_patient_id": cmo_patient_id,
                "dmp_patient_id": dmp_patient_id,
                "tumor_normal": tumor_normal,
            }
        return sample_meta

    def get_nucleo_bams(self, nucleo_runs):
        """
        Collect duplex / simplex / standard bams from the request's nucleo runs.
        Nucleo is run per-sample, so each run contributes one bam per port. The
        sample id is taken from the run's output_metadata (cmoSampleName), which
        matches the fastq-derived key in get_research_sample_metadata().

        Returns a dict keyed by sample id: {sample_id: {duplex, simplex, standard}}
        """
        bams = {}
        for run in nucleo_runs:
            sample_id = (run.output_metadata or {}).get(settings.CMO_SAMPLE_NAME_METADATA_KEY)
            if not sample_id:
                LOGGER.warning("ACCESS Data Analysis: nucleo run %s has no cmoSampleName; skipping", run.pk)
                continue
            entry = bams.setdefault(sample_id, {})
            for port_name, key in (
                (NUCLEO_DUPLEX_PORT, "duplex"),
                (NUCLEO_SIMPLEX_PORT, "simplex"),
                (NUCLEO_STANDARD_PORT, "standard"),
            ):
                bam = self._parse_nucleo_output_port(run, port_name)
                if bam:
                    entry[key] = bam.path
        return bams

    @staticmethod
    def _parse_nucleo_output_port(run, port_name):
        """
        Return the single bam File on the given nucleo output port, or None if the
        port is missing / empty for this run.
        """
        try:
            port = Port.objects.get(name=port_name, run=run.pk)
        except Port.DoesNotExist:
            LOGGER.warning("ACCESS Data Analysis: nucleo run %s has no port %s", run.pk, port_name)
            return None
        bams = [b for b in port.files.all() if b.file_name.endswith(".bam")]
        if not bams:
            LOGGER.warning("ACCESS Data Analysis: nucleo run %s port %s has no bam", run.pk, port_name)
            return None
        return bams[0]

    def get_snv_mafs(self):
        """
        Locate the filtered research mutations MAF for each tumor research_access
        sample, from the "access v2 legacy snv" run for this request.

        Scans the output ports of the most recent completed SNV run and picks files
        matching SNV_FILTERED_MAF_SUFFIX, keying them by the leading sample id in the
        filename, e.g.

            C-ABC123-L001-d.DONOR22-TP.combined-variants.vep_keptrmv_taggedHotspots_fillout_filtered.maf
            -> sample id "C-ABC123-L001-d"

        Returns {sample_id: maf_path}; missing MAFs are simply omitted (schema does
        not require the column).
        """
        mafs = {}
        try:
            snv_runs, _ = get_request_id_runs(SNV_APP_NAMES, [], self.request_id)
        except Exception as e:
            LOGGER.warning(
                "ACCESS Data Analysis: could not find an SNV run for request %s (%s); " "MAF column will be empty",
                self.request_id,
                e,
            )
            return mafs

        for run in snv_runs:
            for port in Port.objects.filter(run=run.pk, port_type=PortType.OUTPUT):
                for f in port.files.all():
                    if f.file_name.endswith(SNV_FILTERED_MAF_SUFFIX):
                        sample_id = f.file_name.split(".")[0]
                        mafs[sample_id] = f.path
        return mafs

    # ~~~ Clinical (DMP) samples ~~~

    def get_clinical_rows(self, cmo_patient_ids, research_maf_by_patient):
        """
        Build samplesheet rows for the clinical_access / clinical_impact samples of
        every CMO patient in ``cmo_patient_ids``.

        DMP bams + metadata come from the "dmp-bams" file group. Each clinical
        sample has several bam File entries (``-duplex`` / ``-simplex`` /
        ``-standard`` / ``-unfilter`` for ACCESS, plain ``.bam`` for IMPACT); they
        are grouped per sample and mapped to the schema's bam columns.

        :param cmo_patient_ids: set[str] - CMO patient ids in the research set (C-XXXX)
        :param research_maf_by_patient: {cmo_patient_id: maf_path}
        :return: list[dict] - samplesheet rows
        """
        # DMP stores the CMO patient id without the "C-" prefix
        dmp_cmo_to_cmo = {self._dmp_cmo(p): p for p in cmo_patient_ids}
        if not dmp_cmo_to_cmo:
            return []

        dmp_files = FileRepository.filter(file_group=DMP_BAM_FILE_GROUP).filter(
            metadata__patient__cmo__in=list(dmp_cmo_to_cmo.keys())
        )

        # group bam File entries by (dmp cmo patient, sample key)
        groups = defaultdict(list)
        for fm in dmp_files:
            f = fm.file
            m = fm.metadata or {}
            if not f.file_name.endswith(".bam"):
                continue
            if m.get("active") is False:
                continue
            patient = m.get("patient") or {}
            dmp_cmo = patient.get("cmo")
            if dmp_cmo not in dmp_cmo_to_cmo:
                continue
            sample_key = m.get("sample") or self._anon_base(m.get("anon_id", ""))
            groups[(dmp_cmo, sample_key)].append(fm)

        rows = []
        for (dmp_cmo, sample_key), fms in sorted(groups.items(), key=lambda kv: str(kv[0])):
            cmo_patient_id = dmp_cmo_to_cmo[dmp_cmo]
            row = self._build_clinical_row(cmo_patient_id, fms, research_maf_by_patient.get(cmo_patient_id, ""))
            if row:
                rows.append(row)
        return rows

    def _build_clinical_row(self, cmo_patient_id, fms, research_maf):
        """
        Turn one clinical sample's DMP bam File entries into a samplesheet row.
        Returns None (and logs) if the assay can't be classified.
        """
        meta = fms[0].metadata or {}
        assay = (meta.get("assay") or "").upper()
        if assay == DMP_CLINICAL_ACCESS_ASSAY:
            assay_type = ASSAY_CLINICAL_ACCESS
        elif assay.startswith(DMP_IMPACT_ASSAY_PREFIXES):
            assay_type = ASSAY_CLINICAL_IMPACT
        else:
            # XS1 clinical ACCESS and any other assay are skipped
            LOGGER.info(
                "ACCESS Data Analysis: skipping DMP sample %s with assay %r",
                meta.get("sample"),
                assay,
            )
            return None

        tumor_normal = "normal" if (meta.get("type") or "").upper().startswith("N") else "tumor"
        dmp_patient_id = (meta.get("patient") or {}).get("dmp") or ""
        anon_id = self._anon_base(meta.get("anon_id", "")) or "NA"
        sample_id = meta.get("sample") or anon_id
        combined_id = "_".join([p for p in [cmo_patient_id, dmp_patient_id] if p])

        # index this sample's bams by type (duplex / simplex / standard / unfilter / plain)
        bams_by_type = {}
        for fm in fms:
            bams_by_type[self._dmp_bam_type(fm.file.file_name)] = fm.file.path

        row = {
            "combined_id": combined_id,
            "cmo_patient_id": cmo_patient_id,
            "dmp_patient_id": dmp_patient_id,
            "sample_id": sample_id,
            "assay_type": assay_type,
            "tumor_normal": tumor_normal,
            "anon_id": anon_id,
            "duplex_bam": "",
            "simplex_bam": "",
            "standard_bam": "",
            "maf": _create_file_object(research_maf) if research_maf else "",
        }

        if assay_type == ASSAY_CLINICAL_ACCESS and tumor_normal == "tumor":
            expected = ("duplex", "simplex")
            for key in expected:
                if key in bams_by_type:
                    row[key + "_bam"] = _create_file_object(bams_by_type[key])
            missing = [k for k in expected if k not in bams_by_type]
            if missing:
                LOGGER.warning(
                    "ACCESS Data Analysis: clinical_access tumor %s missing %s bam(s); have %s",
                    sample_id,
                    "/".join(missing),
                    sorted(bams_by_type),
                )
        else:
            # clinical_access normal -> "-standard.bam"; clinical_impact -> plain "{anon_id}.bam"
            standard = bams_by_type.get("standard") or bams_by_type.get("plain")
            if standard:
                row["standard_bam"] = _create_file_object(standard)
            else:
                LOGGER.warning(
                    "ACCESS Data Analysis: %s sample %s missing standard bam; have %s",
                    assay_type,
                    sample_id,
                    sorted(bams_by_type),
                )
        return row

    @staticmethod
    def _dmp_cmo(cmo_patient_id):
        """C-8VK0V7 -> 8VK0V7 (DMP metadata.patient.cmo has no 'C-' prefix)."""
        return cmo_patient_id[2:] if cmo_patient_id.startswith("C-") else cmo_patient_id

    @staticmethod
    def _anon_base(anon_id):
        """Strip a trailing bam-type suffix: '6789-T-unfilter' -> '6789-T'."""
        if not anon_id:
            return ""
        for suffix in DMP_BAM_SUFFIXES:
            if anon_id.endswith("-" + suffix):
                return anon_id[: -(len(suffix) + 1)]
        return anon_id

    @staticmethod
    def _dmp_bam_type(file_name):
        """Classify a DMP bam by its filename suffix; 'plain' for '{anon_id}.bam'."""
        stem = file_name[:-4] if file_name.endswith(".bam") else file_name
        for suffix in DMP_BAM_SUFFIXES:
            if stem.endswith("-" + suffix):
                return suffix
        return "plain"
