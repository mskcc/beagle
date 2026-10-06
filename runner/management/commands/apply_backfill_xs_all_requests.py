"""
One-time backfill: for every request with a completed "JUNO PIPELINE: access
legacy" run (the specific import batch with the Port.files registration bug),
backfill both the bam-generation ports and whichever of the four
variant-calling workflows (SNV/CNV/SV/MSI) actually have completed runs --
not every request has all four. Purely additive (get_or_create + Port.files
M2M add), same logic already validated per-workflow against 07889_F.

Each request is processed in its own transaction, so a failure on one request
never rolls back earlier ones, and the command continues past errors (logging
them for retry) rather than aborting. Idempotent/resumable: since every write
is gated on port.files.exists() being empty, re-running this after a partial
run (e.g. if it dies partway through) just skips everything already done.

Usage:
    python manage.py apply_backfill_xs_all_requests            # dry run
    python manage.py apply_backfill_xs_all_requests --apply    # actually write
    python manage.py apply_backfill_xs_all_requests --apply --request-ids 07889_F 12345_A

Expect a full unfiltered run to take hours across ~80+ requests; safe to let
it die and restart (or run under nohup/tmux/screen for long unattended runs).
"""
import os
import time
from collections import Counter
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from runner.models import Run, Port, PortType, RunStatus
from file_system.models import File, FileGroup, FileType

BAM_APP_NAME = "JUNO PIPELINE: access legacy"
NUCLEO_APP_NAMES = ["access legacy", "JUNO PIPELINE: access legacy"]
BAM_FILE_GROUP_ID = "02bebece-8f1b-4209-9abf-1a3076b7b07e"

XS1_BAM_PORTS = {
    "duplex": ("duplex_bams", "_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-duplex.bam"),
    "simplex": ("simplex_bams", "_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX-simplex.bam"),
    "unfilter": ("unfiltered_bams", "_cl_aln_srt_MD_IR_FX_BR__aln_srt_IR_FX.bam"),
    "standard": ("standard_bams", "_cl_aln_srt_MD_IR_FX_BR.bam"),
}
ALL_BAM_SUFFIXES = [suffix for _, suffix in XS1_BAM_PORTS.values()] + [".bam", ".bai"]

VARIANT_APP_NAMES = {
    "SNV": ["access legacy SNV", "JUNO PIPELINE: access legacy SNV"],
    "CNV": ["access legacy CNV", "JUNO PIPELINE: access legacy CNV"],
    "SV": ["access legacy SV", "JUNO PIPELINE: access legacy SV"],
    "MSI": ["access legacy MSI", "JUNO PIPELINE: access legacy MSI"],
}
VARIANT_FILE_SUFFIX = {
    "SNV": ".combined-variants.vep_keptrmv_taggedHotspots_fillout_filtered.maf",
    "CNV": "_copynumber_segclusp.genes.txt",
    "SV": "_AllAnnotatedSVs.txt",
    "MSI": "msi_results.txt",
}
VARIANT_FILE_GROUPS = {
    "SNV": "fcec5b6e-905b-4e29-a959-f9d9e28724d3",  # ACCESS SNV
    "MSI": "f3eba1d6-a59e-46fa-bc66-2600bae99c35",  # ACCESS MSI
    "SV": "75202d8b-ed7b-4c6b-9d0d-5de9ef0bfb7d",  # ACCESS SV
    "CNV": "31228842-096b-4196-b92a-1a8370a07608",  # ACCESS CNV
}


# ~~~ shared helpers ~~~


def _file_path(entry):
    location = entry.get("location") or ""
    if location.startswith("file://"):
        return location[len("file://") :]
    return location or entry.get("path")


def _file_type_name(entry, path, file_type_cache_warned=set()):
    ext = entry.get("nameext") or (os.path.splitext(path)[1] if path else "")
    name = ext.lstrip(".").lower() or "unknown"
    max_len = FileType._meta.get_field("name").max_length
    if len(name) > max_len:
        if name not in file_type_cache_warned:
            print(f"    NOTE: FileType name {name!r} ({len(name)} chars) truncated to fit max_length={max_len}")
            file_type_cache_warned.add(name)
        name = name[:max_len]
    return name


def _walk(node):
    if isinstance(node, list):
        found = []
        for item in node:
            found.extend(_walk(item))
        return found
    if not isinstance(node, dict):
        return []
    # some XS1 bam ports (duplex_bams/simplex_bams) wrap the CWL File under
    # {"file": {...}, "sampleId": ..., "patientId": ..., "tumorOrNormal": ...}
    # rather than putting it at the top level.
    wrapped = node.get("file")
    if isinstance(wrapped, dict) and wrapped.get("class") in ("File", "Directory"):
        return _walk(wrapped)
    found = []
    if node.get("class") == "File":
        found.append(node)
        found.extend(_walk(node.get("secondaryFiles") or []))
    elif node.get("class") == "Directory":
        found.extend(_walk(node.get("listing") or []))
    return found


def _sample_key(run):
    tags = run.tags or {}
    val = tags.get("cmoSampleIds") or tags.get("cmoSampleId")
    if isinstance(val, (list, tuple)):
        return val[0] if val else None
    return val


def _sample_id_from_filename(file_name, suffix):
    if suffix.startswith("."):
        return file_name.split(".")[0]
    if suffix.startswith("_") and file_name.endswith(suffix):
        return file_name[: -len(suffix)]
    return None


def _sample_id_for_bam_file(basename):
    for suffix in ALL_BAM_SUFFIXES:
        if basename.endswith(suffix):
            return basename[: -len(suffix)]
    return None


def _patient_id_for_sample(sample_id):
    parts = sample_id.split("-")
    return "-".join(parts[:2]) if len(parts) >= 2 else sample_id


file_type_cache = {}


def _get_file_type(name):
    if name not in file_type_cache:
        file_type_cache[name] = FileType.objects.get_or_create(name=name)[0]
    return file_type_cache[name]


def _link_port(port, entries, request_id, file_group, patient_id, samples, stats, sample_id_fn=None):
    """Create/reuse a File row per entry and link them all to port. sample_id_fn, if given,
    derives per-file patient_id/samples from that file's own basename (bam case)."""
    port_files = []
    for entry in entries:
        path = _file_path(entry)
        if not path:
            stats["skipped_no_path"] += 1
            continue
        basename = entry.get("basename") or os.path.basename(path)
        ext_name = _file_type_name(entry, path)
        stats["file_types"][ext_name] += 1

        if sample_id_fn:
            sample_id = sample_id_fn(basename)
            file_patient_id = _patient_id_for_sample(sample_id) if sample_id else ""
            file_samples = [sample_id] if sample_id else []
        else:
            file_patient_id, file_samples = patient_id, samples

        file_obj, created = File.objects.get_or_create(
            path=path,
            defaults={
                "file_name": basename,
                "original_path": path,
                "file_type": _get_file_type(ext_name),
                "size": entry.get("size") or 0,
                "file_group": file_group,
                "checksum": entry.get("checksum") or None,
                "request_id": request_id,
                "patient_id": file_patient_id,
                "samples": file_samples,
            },
        )
        stats["files_created" if created else "files_reused"] += 1
        port_files.append(file_obj)

    if port_files:
        port.files.add(*port_files)
        stats["links_added"] += len(port_files)


def _backfill_bams(request_id, stats):
    bam_group = FileGroup.objects.get(pk=BAM_FILE_GROUP_ID)
    runs = Run.objects.filter(
        tags__igoRequestId=request_id, app__name__in=NUCLEO_APP_NAMES, status=RunStatus.COMPLETED
    ).order_by("-created_date")
    for run in runs:
        for port_name, _suffix in XS1_BAM_PORTS.values():
            port = Port.objects.filter(name=port_name, run=run.pk).first()
            if not port or port.files.exists() or not port.value:
                continue
            entries = _walk(port.value)
            if entries:
                _link_port(
                    port, entries, request_id, bam_group, "", [], stats, sample_id_fn=_sample_id_for_bam_file
                )


def _latest_runs_by_sample(request_id, app_names):
    runs = Run.objects.filter(
        tags__igoRequestId=request_id, app__name__in=app_names, status=RunStatus.COMPLETED
    ).order_by("-created_date")
    latest = {}
    for run in runs:
        key = _sample_key(run) or str(run.pk)
        latest.setdefault(key, run)
    return latest


def _backfill_variant(request_id, label, stats):
    app_names = VARIANT_APP_NAMES[label]
    suffix = VARIANT_FILE_SUFFIX[label]
    file_group = FileGroup.objects.get(pk=VARIANT_FILE_GROUPS[label])
    latest = _latest_runs_by_sample(request_id, app_names)
    for run in latest.values():
        run_sample_id = _sample_key(run)
        patient_id = _patient_id_for_sample(run_sample_id) if run_sample_id else ""
        samples = [run_sample_id] if run_sample_id else []
        for port in Port.objects.filter(run=run.pk, port_type=PortType.OUTPUT):
            if port.files.exists() or not port.value:
                continue
            entries = _walk(port.value)
            if entries:
                _link_port(port, entries, request_id, file_group, patient_id, samples, stats)


def backfill_request(request_id, apply_changes):
    stats = {
        "files_created": 0,
        "files_reused": 0,
        "links_added": 0,
        "skipped_no_path": 0,
        "file_types": Counter(),
    }
    with transaction.atomic():
        _backfill_bams(request_id, stats)
        for label in VARIANT_APP_NAMES:
            _backfill_variant(request_id, label, stats)
        if not apply_changes:
            transaction.set_rollback(True)
    return stats


def _ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Command(BaseCommand):
    help = (
        "Backfill Port.files/File registration for XS1 (v1 ACCESS) bam-generation and "
        "SNV/CNV/SV/MSI runs that were imported via 'JUNO PIPELINE:' and never got their "
        "output files linked. Purely additive; dry-run by default."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually write. Without this flag, every request's transaction is rolled back (dry run).",
        )
        parser.add_argument(
            "--request-ids",
            type=str,
            nargs="+",
            help="Only process these specific request ids, instead of discovering every request with a "
            "completed 'JUNO PIPELINE: access legacy' run.",
        )

    def handle(self, *args, **options):
        apply_changes = options["apply"]
        request_ids = options.get("request_ids")

        if not request_ids:
            bam_runs = Run.objects.filter(app__name=BAM_APP_NAME, status=RunStatus.COMPLETED)
            request_ids = sorted({rid for rid in bam_runs.values_list("tags__igoRequestId", flat=True) if rid})

        print(f"[{_ts()}] {len(request_ids)} request(s) to process. APPLY={apply_changes}")

        start = time.monotonic()
        totals = Counter()
        failed = []

        for i, request_id in enumerate(request_ids):
            t0 = time.monotonic()
            try:
                stats = backfill_request(request_id, apply_changes)
            except Exception as e:
                failed.append(request_id)
                print(f"[{_ts()}] [{i + 1}/{len(request_ids)}] {request_id}: FAILED -- {e!r}")
                continue
            elapsed = time.monotonic() - t0
            totals["files_created"] += stats["files_created"]
            totals["files_reused"] += stats["files_reused"]
            totals["links_added"] += stats["links_added"]
            print(
                f"[{_ts()}] [{i + 1}/{len(request_ids)}] {request_id}: "
                f"created={stats['files_created']} reused={stats['files_reused']} "
                f"linked={stats['links_added']} ({elapsed:.1f}s)"
            )

        total_elapsed = time.monotonic() - start
        print("=" * 60)
        print(f"[{_ts()}] DONE")
        print(f"requests processed: {len(request_ids) - len(failed)} / {len(request_ids)}")
        print(f"failed requests: {failed}")
        print(f"File rows created: {totals['files_created']}")
        print(f"File rows reused:  {totals['files_reused']}")
        print(f"Port.files links added: {totals['links_added']}")
        print(f"total elapsed: {total_elapsed / 60:.1f} minutes")
        print(
            "APPLY was False -- every transaction rolled back, nothing committed."
            if not apply_changes
            else "APPLY was True -- changes committed."
        )
