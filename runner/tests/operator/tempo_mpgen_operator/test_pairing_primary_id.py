"""Tests for the primary_id columns added to the tempo pairing file.

The pairing file keeps its historical two columns (NORMAL_ID, TUMOR_ID as
cmoSampleNames) and gains NORMAL_PRIMARY_ID / TUMOR_PRIMARY_ID as a third
and fourth column, so existing consumers (including
``load_pairing_file``, which reads only row[0]/row[1]) are unaffected.
"""
from types import SimpleNamespace

from django.test import SimpleTestCase

from runner.operator.tempo_mpgen_operator.bin.tempo_patient import Patient
from runner.operator.tempo_mpgen_operator.bin.tempo_sample import TempoSample


def _file(metadata, path):
    """A file_list entry: .file carries the path, .metadata the LIMS data."""
    return SimpleNamespace(file=SimpleNamespace(path=path), metadata=metadata)


def _sample_files(primary_id, cmo_name, patient_id, side):
    base = {
        "primaryId": primary_id,
        "cmoSampleName": cmo_name,
        "cmoPatientId": patient_id,
        "sampleClass": "WGS",
        "sampleType": side,
        "baitSet": "SureSelect-All-Exon-V4-hg19",
        "runMode": "NovaSeq 6000",
    }
    return [
        _file(dict(base, R="R1"), "/fastqs/%s_R1.fastq.gz" % cmo_name),
        _file(dict(base, R="R2"), "/fastqs/%s_R2.fastq.gz" % cmo_name),
    ]


class TestTempoSamplePrimaryId(SimpleTestCase):
    def test_primary_id_exposed_on_valid_sample(self):
        files = _sample_files("PID-N1", "C-001-N001", "P-001", "Normal")
        sample = TempoSample("C-001-N001", files)
        self.assertFalse(sample.conflict)
        self.assertEqual(sample.primary_id, "PID-N1")


class TestPatientPairingString(SimpleTestCase):
    def test_pairing_string_carries_primary_ids(self):
        tumor_files = _sample_files("PID-T1", "C-001-T001", "P-001", "Tumor")
        normal_files = _sample_files("PID-N1", "C-001-N001", "P-001", "Normal")
        patient = Patient("P-001", tumor_files + normal_files)
        self.assertTrue(patient.sample_pairing, "fixture did not pair")
        pairing = patient.create_pairing_string()
        self.assertEqual(
            pairing,
            "C-001-N001\tC-001-T001\tPID-N1\tPID-T1\n",
        )

    def test_first_two_columns_unchanged(self):
        # historical consumers read only the first two columns
        tumor_files = _sample_files("PID-T1", "C-001-T001", "P-001", "Tumor")
        normal_files = _sample_files("PID-N1", "C-001-N001", "P-001", "Normal")
        patient = Patient("P-001", tumor_files + normal_files)
        row = patient.create_pairing_string().strip().split("\t")
        self.assertEqual(row[0], "C-001-N001")
        self.assertEqual(row[1], "C-001-T001")
