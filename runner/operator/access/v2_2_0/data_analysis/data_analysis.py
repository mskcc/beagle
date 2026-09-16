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

# ~~~ Upstream pipelines (Run.app.name) ~~~
NUCLEO_APP_NAMES = ["access v2 nucleo", "access nucleo"]  # duplex / simplex / unfilter / standard bams
SNV_APP_NAMES = ["access v2 legacy SNV"]  # research mutations MAF
CNV_APP_NAMES = ["access v2 legacy CNV"]  # research copy-number genes file
SV_APP_NAMES = ["access v2 legacy SV"]  # research structural-variant file
MSI_APP_NAMES = ["access v2 legacy MSI"]  # research MSI results file

# ~~~ Nucleo output ports -> schema bam column ~~~
# The nucleo port names are legacy/misleading; mapping verified against a real run:
#   fgbio_filter_consensus_reads_duplex_bam -> {s}_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam
#   fgbio_postprocessing_simplex_bam        -> {s}_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-simplex.bam
#   fgbio_collapsed_bam                      -> {s}_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam   (unfilter)
#   uncollapsed_bam                          -> {s}_cl_aln_srt_MD_IR_FX_BR.bam                  (standard)
NUCLEO_DUPLEX_PORT = "fgbio_filter_consensus_reads_duplex_bam"
NUCLEO_SIMPLEX_PORT = "fgbio_postprocessing_simplex_bam"
NUCLEO_UNFILTER_PORT = "fgbio_collapsed_bam"
NUCLEO_STANDARD_PORT = "uncollapsed_bam"

# ~~~ Variant-file filenames on the respective pipeline output ports ~~~
# maf: {s}.<normal>.combined-variants.vep_keptrmv_taggedHotspots_fillout_filtered.maf
SNV_MAF_SUFFIX = ".combined-variants.vep_keptrmv_taggedHotspots_fillout_filtered.maf"
CNV_FILE_SUFFIX = "_copynumber_segclusp.genes.txt"
SV_FILE_SUFFIX = "_AllAnnotatedSVs.txt"
MSI_FILE_SUFFIX = "msi_results.txt"  # no sample id in the name -> keyed off the run

# accessanalysis samplesheet assay_type values
ASSAY_RESEARCH_ACCESS = "research_access"
ASSAY_CLINICAL_ACCESS = "clinical_access"
ASSAY_CLINICAL_IMPACT = "clinical_impact"

# ~~~ DMP (clinical) bams ~~~
# "dmp-bams" file group. Clinical bams + metadata live here (not in nucleo ports).
DMP_BAM_FILE_GROUP = "d4775633-f53f-412f-afa5-46e9a86b654b"
# metadata.assay: exactly "XS2" -> clinical ACCESS (XS1 excluded); IM*/IH* -> clinical IMPACT.
DMP_CLINICAL_ACCESS_ASSAY = "XS2"
DMP_IMPACT_ASSAY_PREFIXES = ("IM", "IH")
# DMP bam filename suffixes (the anon_id carries the same suffix in metadata)
DMP_BAM_SUFFIXES = ("duplex", "simplex", "standard", "unfilter")

# Columns emitted for every row, in schema order. Missing values are "".
SAMPLESHEET_COLUMNS = [
    "combined_id",
    "cmo_patient_id",
    "dmp_patient_id",
    "sex",
    "sample_id",
    "assay_type",
    "tumor_normal",
    "anon_id",
    "access_version",
    "duplex_bam",
    "simplex_bam",
    "unfilter_bam",
    "standard_bam",
    "maf",
    "cna_file",
    "sv_file",
    "msi_file",
]


def _create_file_object(path):
    """
    Create a simple CWL File object from a path. The nextflow template processor
    converts these into paths when it renders the samplesheet CSV.
    """
    return {"class": "File", "location": "iris://" + path}


def _blank_row():
    return {c: "" for c in SAMPLESHEET_COLUMNS}


def _access_version_from_bait_set(bait_set):
    """
    'MSK-ACCESS-v1_0-probesAllwFP_GRCh38' -> 'XS1'
    'MSK-ACCESS-v2_0-...'                 -> 'XS2'
    anything else                         -> '' (blank)
    """
    b = (bait_set or "").upper().replace("_", "").replace("-", "")
    if "ACCESSV1" in b:
        return "XS1"
    if "ACCESSV2" in b:
        return "XS2"
    return ""


class AccessV2DataAnalysisOperator(Operator):
    """
    Operator for the access_data_analysis_nf workflow. Builds the Voyager-prepared
    samplesheet described by ``assets/schema_input.json``:

        combined_id, cmo_patient_id, dmp_patient_id, sex, sample_id, assay_type,
        tumor_normal, anon_id, access_version, duplex_bam, simplex_bam,
        unfilter_bam, standard_bam, maf, cna_file, sv_file, msi_file

    Downstream of the ACCESS nucleo, SNV, CNV, SV and MSI operators.

    research_access rows (from the request's fastq metadata + nucleo/variant runs):
      - sex           <- fastq `sex`
      - access_version<- fastq `baitSet` (MSK-ACCESS-v1* -> XS1, -v2* -> XS2)
      - standard_bam  <- nucleo `uncollapsed_bam` port          (every sample)
      - unfilter_bam  <- nucleo `fgbio_collapsed_bam` port      (normal only)
      - duplex_bam    <- nucleo `fgbio_filter_consensus_reads_duplex_bam` (tumor)
      - simplex_bam   <- nucleo `fgbio_postprocessing_simplex_bam`        (tumor)
      - maf / cna_file / sv_file / msi_file  <- SNV / CNV / SV / MSI run
        output ports                                            (tumor only)

    Clinical rows (clinical_access assay "XS2", clinical_impact assay "IM*"/"IH*"),
    pulled for every CMO patient in the research set from the "dmp-bams" file group:
      - sex           <- the patient's research `sex`
      - access_version<- blank (non-research)
      - clinical_access tumor  -> duplex_bam + simplex_bam + standard_bam
      - clinical_access normal -> unfilter_bam + standard_bam
      - clinical_impact (any)  -> standard_bam (plain "{anon_id}.bam")
      - maf   <- the patient's research MAF (so the MAF-merge step picks it up)
      - cna_file / sv_file / msi_file  <- blank (research-only columns)
    """

    def get_jobs(self):
        LOGGER.info("Operator JobGroupNotifier ID %s", self.job_group_notifier_id)
        app = self.get_pipeline_id()
        pipeline = Pipeline.objects.get(id=app)
        run_date = datetime.now().strftime("%Y%m%d_%H:%M:%f")

        # Resolve the request + its most recent completed nucleo runs.
        # get_request_id_runs raises a bare AttributeError when nothing matches.
        try:
            nucleo_runs, self.request_id = get_request_id_runs(NUCLEO_APP_NAMES, self.run_ids, self.request_id)
        except AttributeError:
            raise Exception(
                "ACCESS Data Analysis: no completed nucleo run ({}) found for request {} / run_ids {}".format(
                    " / ".join(NUCLEO_APP_NAMES), self.request_id, self.run_ids
                )
            )

        sample_meta = self.get_research_sample_metadata()  # keyed by cmoSampleName
        nucleo_bams = self.get_nucleo_bams(nucleo_runs)  # {sample_id: {duplex, simplex, unfilter, standard}}

        # Per-sample research variant files (tumor samples only)
        snv_mafs = self.get_variant_files(SNV_APP_NAMES, SNV_MAF_SUFFIX, "maf")
        cna_files = self.get_variant_files(CNV_APP_NAMES, CNV_FILE_SUFFIX, "cna_file")
        sv_files = self.get_variant_files(SV_APP_NAMES, SV_FILE_SUFFIX, "sv_file")
        msi_files = self.get_variant_files(MSI_APP_NAMES, MSI_FILE_SUFFIX, "msi_file")

        # Per-patient rollups for the clinical rows
        research_maf_by_patient = self._first_by_patient(snv_mafs, "research MAF")
        sex_by_patient = {}
        for m in sample_meta.values():
            if m["cmo_patient_id"] and m["sex"]:
                sex_by_patient.setdefault(m["cmo_patient_id"], m["sex"])

        rows = []
        for sample_id, meta in sample_meta.items():
            bams = nucleo_bams.get(sample_id, {})
            row = _blank_row()
            row.update(
                {
                    "combined_id": meta["combined_id"],
                    "cmo_patient_id": meta["cmo_patient_id"],
                    "dmp_patient_id": meta["dmp_patient_id"],
                    "sex": meta["sex"],
                    "sample_id": sample_id,
                    "assay_type": ASSAY_RESEARCH_ACCESS,
                    "tumor_normal": meta["tumor_normal"],
                    "anon_id": "NA",
                    "access_version": meta["access_version"],
                }
            )
            # standard_bam: every sample
            if bams.get("standard"):
                row["standard_bam"] = _create_file_object(bams["standard"])
            if meta["tumor_normal"] == "tumor":
                if bams.get("duplex"):
                    row["duplex_bam"] = _create_file_object(bams["duplex"])
                if bams.get("simplex"):
                    row["simplex_bam"] = _create_file_object(bams["simplex"])
                for col, table in (
                    ("maf", snv_mafs),
                    ("cna_file", cna_files),
                    ("sv_file", sv_files),
                    ("msi_file", msi_files),
                ):
                    if table.get(sample_id):
                        row[col] = _create_file_object(table[sample_id])
            else:
                if bams.get("unfilter"):
                    row["unfilter_bam"] = _create_file_object(bams["unfilter"])
            rows.append(row)

        if not rows:
            raise Exception(
                "ACCESS Data Analysis: no research_access samples found for request {}".format(self.request_id)
            )

        # Clinical (DMP) samples for every CMO patient seen in the research set
        cmo_patient_ids = {m["cmo_patient_id"] for m in sample_meta.values() if m["cmo_patient_id"]}
        rows.extend(self.get_clinical_rows(cmo_patient_ids, research_maf_by_patient, sex_by_patient))

        job_json = {
            "name": "ACCESS Data Analysis: {request_id}, {run_date}".format(
                request_id=self.request_id, run_date=run_date
            ),
            "app": app,
            "inputs": {"input": rows},
            "tags": {
                settings.REQUEST_ID_METADATA_KEY: self.request_id,
                "pipeline": pipeline.name,
                "pipeline_version": pipeline.version,
            },
            "output_metadata": {},
        }
        return [RunCreator(**job_json)]

    # ~~~ research_access ~~~

    def get_research_sample_metadata(self):
        """
        Per-sample metadata from the request's fastq files (same query nucleo uses).
        Returns a dict keyed by cmoSampleName:

            {sample_id: {combined_id, cmo_patient_id, dmp_patient_id, sex,
                         access_version, tumor_normal}}
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
            # Research samples have no DMP patient id in Voyager; combined_id is the CMO id.
            dmp_patient_id = ""
            combined_id = "_".join([p for p in [cmo_patient_id, dmp_patient_id] if p])

            tumor_normal = (m.get(settings.TUMOR_OR_NORMAL_METADATA_KEY) or "").strip().lower()
            tumor_normal = "tumor" if tumor_normal.startswith("t") else "normal"

            sex = (m.get("sex") or "").strip().upper()[:1]
            if sex not in ("M", "F"):
                LOGGER.warning("ACCESS Data Analysis: sample %s has no usable sex (%r)", sample_id, m.get("sex"))
                sex = ""

            access_version = _access_version_from_bait_set(m.get("baitSet"))
            if not access_version:
                LOGGER.warning(
                    "ACCESS Data Analysis: sample %s baitSet %r did not resolve to XS1/XS2",
                    sample_id,
                    m.get("baitSet"),
                )

            sample_meta[sample_id] = {
                "combined_id": combined_id,
                "cmo_patient_id": cmo_patient_id,
                "dmp_patient_id": dmp_patient_id,
                "sex": sex,
                "access_version": access_version,
                "tumor_normal": tumor_normal,
            }
        return sample_meta

    def get_nucleo_bams(self, nucleo_runs):
        """
        Collect duplex / simplex / unfilter / standard bams from the request's nucleo
        runs (one run per sample). Keyed by the run's output_metadata cmoSampleName,
        which matches the fastq-derived key in get_research_sample_metadata().
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
                (NUCLEO_UNFILTER_PORT, "unfilter"),
                (NUCLEO_STANDARD_PORT, "standard"),
            ):
                bam = self._parse_nucleo_output_port(run, port_name)
                if bam:
                    entry[key] = bam.path
        return bams

    @staticmethod
    def _parse_nucleo_output_port(run, port_name):
        """The single bam File on a nucleo output port, or None if missing / empty."""
        try:
            port = Port.objects.get(name=port_name, run=run.pk)
        except Port.DoesNotExist:
            LOGGER.warning("ACCESS Data Analysis: nucleo run %s has no port %s", run.pk, port_name)
            return None
        port_bams = [b for b in port.files.all() if b.file_name.endswith(".bam")]
        if not port_bams:
            LOGGER.warning("ACCESS Data Analysis: nucleo run %s port %s has no bam", run.pk, port_name)
            return None
        return port_bams[0]

    def get_variant_files(self, app_names, filename_suffix, label):
        """
        Scan the most recent completed run of ``app_names`` (SNV / CNV / SV / MSI)
        for output-port files ending in ``filename_suffix``, keyed by sample id.

        Sample id comes from the run (output_metadata cmoSampleName for SNV; tags
        cmoSampleIds for CNV / SV / MSI); for MSI the filename carries no sample id
        so the run key is required.

        Returns {sample_id: path}; empty (and logs) when no such run exists.
        """
        result = {}
        try:
            runs, _ = get_request_id_runs(app_names, [], self.request_id)
        except Exception as e:
            LOGGER.warning(
                "ACCESS Data Analysis: no %s run for request %s (%s); %s column will be empty",
                " / ".join(app_names),
                self.request_id,
                e,
                label,
            )
            return result

        for run in runs:
            run_sample_id = self._run_sample_id(run)
            for port in Port.objects.filter(run=run.pk, port_type=PortType.OUTPUT):
                for f in port.files.all():
                    if not f.file_name.endswith(filename_suffix):
                        continue
                    key = run_sample_id or self._sample_id_from_filename(f.file_name, filename_suffix)
                    if not key:
                        LOGGER.warning(
                            "ACCESS Data Analysis: cannot determine sample for %s (run %s)", f.file_name, run.pk
                        )
                        continue
                    result.setdefault(key, f.path)
        return result

    @staticmethod
    def _run_sample_id(run):
        om = run.output_metadata or {}
        if om.get(settings.CMO_SAMPLE_NAME_METADATA_KEY):
            return om[settings.CMO_SAMPLE_NAME_METADATA_KEY]
        tags = run.tags or {}
        val = tags.get("cmoSampleIds") or tags.get("cmoSampleId") or tags.get(settings.CMO_SAMPLE_NAME_METADATA_KEY)
        if isinstance(val, (list, tuple)):
            return val[0] if val else None
        return val

    @staticmethod
    def _sample_id_from_filename(file_name, filename_suffix):
        if filename_suffix.startswith("."):
            return file_name.split(".")[0]
        if filename_suffix.startswith("_") and file_name.endswith(filename_suffix):
            return file_name[: -len(filename_suffix)]
        return None

    @staticmethod
    def _first_by_patient(by_sample, label):
        """Collapse {sample_id: path} to {cmo_patient_id: path}, first wins."""
        by_patient = {}
        for sample_id, path in by_sample.items():
            patient = "-".join(sample_id.split("-")[:2])
            existing = by_patient.get(patient)
            if existing and existing != path:
                LOGGER.warning(
                    "ACCESS Data Analysis: patient %s has multiple %ss; keeping %s, ignoring %s",
                    patient,
                    label,
                    existing,
                    path,
                )
                continue
            by_patient[patient] = path
        return by_patient

    # ~~~ Clinical (DMP) samples ~~~

    def get_clinical_rows(self, cmo_patient_ids, research_maf_by_patient, sex_by_patient):
        """
        Build samplesheet rows for the clinical_access / clinical_impact samples of
        every CMO patient in ``cmo_patient_ids``. DMP bams + metadata come from the
        "dmp-bams" file group; each clinical sample has several bam File entries
        (``-duplex`` / ``-simplex`` / ``-standard`` / ``-unfilter`` for ACCESS, plain
        ``.bam`` for IMPACT), grouped per sample and mapped to the schema's columns.
        """
        # DMP stores the CMO patient id without the "C-" prefix
        dmp_cmo_to_cmo = {self._dmp_cmo(p): p for p in cmo_patient_ids}
        if not dmp_cmo_to_cmo:
            return []

        dmp_files = FileRepository.filter(file_group=DMP_BAM_FILE_GROUP).filter(
            metadata__patient__cmo__in=list(dmp_cmo_to_cmo.keys())
        )

        groups = defaultdict(list)
        for fm in dmp_files:
            f = fm.file
            m = fm.metadata or {}
            if not f.file_name.endswith(".bam"):
                continue
            if m.get("active") is False:
                continue
            dmp_cmo = (m.get("patient") or {}).get("cmo")
            if dmp_cmo not in dmp_cmo_to_cmo:
                continue
            sample_key = m.get("sample") or self._anon_base(m.get("anon_id", ""))
            groups[(dmp_cmo, sample_key)].append(fm)

        rows = []
        for (dmp_cmo, _sample_key), fms in sorted(groups.items(), key=lambda kv: str(kv[0])):
            cmo_patient_id = dmp_cmo_to_cmo[dmp_cmo]
            row = self._build_clinical_row(
                cmo_patient_id,
                fms,
                research_maf_by_patient.get(cmo_patient_id, ""),
                sex_by_patient.get(cmo_patient_id, ""),
            )
            if row:
                rows.append(row)
        return rows

    def _build_clinical_row(self, cmo_patient_id, fms, research_maf, sex):
        """
        One clinical sample's DMP bam File entries -> a samplesheet row.
        Returns None (and logs) if the assay can't be classified.
        """
        meta = fms[0].metadata or {}
        assay = (meta.get("assay") or "").upper()
        if assay == DMP_CLINICAL_ACCESS_ASSAY:
            assay_type = ASSAY_CLINICAL_ACCESS
        elif assay.startswith(DMP_IMPACT_ASSAY_PREFIXES):
            assay_type = ASSAY_CLINICAL_IMPACT
        else:
            LOGGER.info("ACCESS Data Analysis: skipping DMP sample %s with assay %r", meta.get("sample"), assay)
            return None

        tumor_normal = "normal" if (meta.get("type") or "").upper().startswith("N") else "tumor"
        dmp_patient_id = (meta.get("patient") or {}).get("dmp") or ""
        anon_id = self._anon_base(meta.get("anon_id", "")) or "NA"
        sample_id = meta.get("sample") or anon_id

        if not sex:
            LOGGER.warning(
                "ACCESS Data Analysis: no research sex for patient %s; clinical sample %s sex left blank",
                cmo_patient_id,
                sample_id,
            )

        row = _blank_row()
        row.update(
            {
                "combined_id": "_".join([p for p in [cmo_patient_id, dmp_patient_id] if p]),
                "cmo_patient_id": cmo_patient_id,
                "dmp_patient_id": dmp_patient_id,
                "sex": sex,
                "sample_id": sample_id,
                "assay_type": assay_type,
                "tumor_normal": tumor_normal,
                "anon_id": anon_id,
                "access_version": "",
                "maf": _create_file_object(research_maf) if research_maf else "",
            }
        )

        # bam-column -> ordered list of acceptable DMP bam types
        if assay_type == ASSAY_CLINICAL_ACCESS:
            if tumor_normal == "tumor":
                wanted = {"duplex_bam": ("duplex",), "simplex_bam": ("simplex",), "standard_bam": ("standard",)}
            else:
                wanted = {"unfilter_bam": ("unfilter",), "standard_bam": ("standard",)}
        else:  # clinical_impact
            wanted = {"standard_bam": ("plain", "standard")}

        bams_by_type = {self._dmp_bam_type(fm.file.file_name): fm.file.path for fm in fms}
        for col, types in wanted.items():
            path = next((bams_by_type[t] for t in types if t in bams_by_type), None)
            if path:
                row[col] = _create_file_object(path)
            else:
                LOGGER.warning(
                    "ACCESS Data Analysis: %s %s sample %s missing %s bam; have %s",
                    assay_type,
                    tumor_normal,
                    sample_id,
                    col,
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
