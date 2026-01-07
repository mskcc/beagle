"""
Test for constructing Argos samples
"""
from uuid import UUID
from django.conf import settings
from django.test import TestCase
from runner.operator.argos_operator.v2_3_0.bin.make_sample import Fastqs, build_sample

from file_system.models import File, FileGroup, FileMetadata, FileType
import json


class TestMakeSample(TestCase):
    fixtures = [
        "file_system.filegroup.json",
        "file_system.storage.json"
    ]

    def test_build_sample1(self):
        """
        Test for building a sample
        """
        data = [
            {
                "file_name": "JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R1_001.fastq.gz",
                "id": UUID("a46c5e6b-0793-4cd2-b5dd-92b3d71cf1ac"),
                "metadata": {
                    "R": "R1",
                    "baitSet": "IMPACT468_BAITS",
                    "barcodeId": None,
                    "barcodeIndex": None,
                    "captureConcentrationNm": "10.377358490566039",
                    "captureInputNg": "110.0",
                    "captureName": "Pool-05257_CD-06287_AY-10075_D_2-Tube2_1",
                    settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Normal",
                    "collectionYear": "",
                    "dataAnalystEmail": "",
                    "dataAnalystName": "",
                    "externalSampleId": "JW_MEL_007_NORM",
                    "flowCellId": "HCYYWBBXY",
                    "flowCellLanes": [1, 2, 3],
                    settings.IGO_COMPLETE_METADATA_KEY: True,
                    "investigatorEmail": "email2@internet.com",
                    "investigatorName": "Jane Doe",
                    "investigatorSampleId": "JW_MEL_007_NORM",
                    "labHeadEmail": "email@internet.com",
                    "labHeadName": "John Smith",
                    "libraryConcentrationNgul": 10.6,
                    settings.LIBRARY_ID_METADATA_KEY: "10075_D_2_3",
                    "libraryVolume": None,
                    settings.ONCOTREE_METADATA_KEY: None,
                    settings.PATIENT_ID_METADATA_KEY: "C-8VK0V7",
                    "piEmail": "",
                    "preservation": "EDTA-Streck",
                    "projectManagerName": "",
                    "readLength": "101/8/8/101",
                    settings.RECIPE_METADATA_KEY: "IMPACT468",
                    settings.REQUEST_ID_METADATA_KEY: "10075_D_2",
                    "sequencingCenter": "MSKCC",
                    "platform": "Illumina",
                    "runDate": "2019-12-12",
                    "runId": "JAX_0397",
                    "runMode": "HiSeq High Output",
                    settings.SAMPLE_ID_METADATA_KEY: "10075_D_2_3",
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: "C-8VK0V7-N001-d",
                    "sampleOrigin": "Plasma",
                    "sex": "F",
                    "species": "Human",
                    settings.SAMPLE_CLASS_METADATA_KEY: "Blood",
                    "tissueLocation": "",
                    "tumorOrNormal": "Normal",
                },
                "path": "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_2/Sample_JW_MEL_007_NORM_IGO_10075_D_2_3/JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R1_001.fastq.gz",
            },
            {
                "file_name": "JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R2_001.fastq.gz",
                "id": UUID("c71c259a-ebc0-4490-9af1-bc99387a70d7"),
                "metadata": {
                    "R": "R2",
                    "baitSet": "IMPACT468_BAITS",
                    "barcodeId": None,
                    "barcodeIndex": None,
                    "captureConcentrationNm": "10.377358490566039",
                    "captureInputNg": "110.0",
                    "captureName": "Pool-05257_CD-06287_AY-10075_D_2-Tube2_1",
                    settings.CMO_SAMPLE_CLASS_METADATA_KEY: "Normal",
                    "collectionYear": "",
                    "dataAnalystEmail": "",
                    "dataAnalystName": "",
                    "externalSampleId": "JW_MEL_007_NORM",
                    "flowCellId": "HCYYWBBXY",
                    "flowCellLanes": [1, 2, 3],
                    settings.IGO_COMPLETE_METADATA_KEY: True,
                    "investigatorEmail": "email2@internet.com",
                    "investigatorName": "Jane Doe",
                    "investigatorSampleId": "JW_MEL_007_NORM",
                    "labHeadEmail": "email@internet.com",
                    "labHeadName": "John Smith",
                    "libraryConcentrationNgul": 10.6,
                    "libraryIgoId": None,
                    "libraryVolume": None,
                    settings.ONCOTREE_METADATA_KEY: None,
                    settings.PATIENT_ID_METADATA_KEY: "C-8VK0V7",
                    "piEmail": "",
                    "preservation": "EDTA-Streck",
                    "projectManagerName": "",
                    "readLength": "101/8/8/101",
                    settings.RECIPE_METADATA_KEY: "IMPACT468",
                    settings.REQUEST_ID_METADATA_KEY: "10075_D_2",
                    "sequencingCenter": "MSKCC",
                    "platform": "Illumina",
                    "runDate": "2019-12-12",
                                "runId": "JAX_0397",
                    "runMode": "HiSeq High Output",
                    settings.SAMPLE_ID_METADATA_KEY: "10075_D_2_3",
                    settings.CMO_SAMPLE_NAME_METADATA_KEY: "C-8VK0V7-N001-d",
                    "sampleOrigin": "Plasma",
                    "sex": "F",
                    "species": "Human",
                    settings.SAMPLE_CLASS_METADATA_KEY: "Blood",
                    "tissueLocation": "",
                    "tumorOrNormal": "Normal",
                },
                "path": "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_2/Sample_JW_MEL_007_NORM_IGO_10075_D_2_3/JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R2_001.fastq.gz",
            },
        ]

        r1_bid = ""
        r2_bid = ""
        for i in data:
            if i["metadata"]["R"] == "R1":
                r1_bid= i["id"]
            else:
                r2_bid= i["id"]
            f = File.objects.create(
                file_type = FileType.objects.create(name="fastq"),
                file_group = FileGroup.objects.get(id=settings.IMPORT_FILE_GROUP),
                file_name = i["file_name"],
                path = i["path"]
            )
            FileMetadata.objects.create_or_update(
                file=f,
                metadata=i["metadata"]
            )

        sample = build_sample(data)
        sample["R1_bid"] = []
        sample["R2_bid"] = []

        expected_sample = {
            "CN": "MSKCC",
            "ID": ["s_C_8VK0V7_N001_d_HCYYWBBXY"],
            "LB": "10075_D_2_3",
            "PL": "Illumina",
            "PU": ["HCYYWBBXY"],
            "R1": [
                "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_2/Sample_JW_MEL_007_NORM_IGO_10075_D_2_3/JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R1_001.fastq.gz"
            ],
            "R1_bid": [],
            "R2": [
                "/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_2/Sample_JW_MEL_007_NORM_IGO_10075_D_2_3/JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R2_001.fastq.gz"
            ],
            "R2_bid": [],
            "bam": [],
            "bam_bid": [],
            "SM": "s_C_8VK0V7_N001_d",
            "bait_set": "IMPACT468_BAITS",
            "sample_id": "10075_D_2_3",
            "sample_origin": ["Plasma"],
            "patient_id": "C-8VK0V7",
            "request_id": "10075_D_2",
            "run_date": ["2019-12-12"],
            "run_id": ["JAX_0397"],
            "run_mode": "hiseq",
            "preservation_type": ["EDTA-Streck"],
            "species": "Human",
            "specimen_type": "Blood",
            "tumor_type": "Normal",
            "pi": "John Smith",
            "pi_email": "email@internet.com",
        }

        print("Testing build_sample ---")
        print(json.dumps(sample, cls=UUIDEncoder))
        print()
        print(json.dumps(expected_sample, cls=UUIDEncoder))

        from pprint import pprint
        pprint(dict_diff(sample, expected_sample))

        self.assertTrue(sample == expected_sample)


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)

def dict_diff(d1, d2, path=""):
    diffs = {}

    # Keys present in either dictionary
    keys = set(d1.keys()) | set(d2.keys())

    for key in keys:
        v1 = d1.get(key, "__MISSING__")
        v2 = d2.get(key, "__MISSING__")
        current_path = f"{path}.{key}" if path else key

        if isinstance(v1, dict) and isinstance(v2, dict):
            # Recurse into nested dictionaries
            nested = dict_diff(v1, v2, current_path)
            if nested:
                diffs.update(nested)
        else:
            if v1 != v2:
                diffs[current_path] = {"old": v1, "new": v2}

    return diffs
