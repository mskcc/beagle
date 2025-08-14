import csv
from pathlib import Path
from pprint import pprint

from django.conf import settings

from file_system.repository.file_repository import FileRepository
from runner.run.processors.file_processor import FileProcessor

from .files_object import FilesObj
from .helpers import spoof_barcode
from .sample_file_object import SampleFile

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CSV_PATH = PROJECT_ROOT / "assets" / "pooled_normals.csv"
POOLED_NORMALS = {}

REQUIRED_KEYS = [
    settings.CMO_SAMPLE_NAME_METADATA_KEY,  # cmoSampleName
    settings.REQUEST_ID_METADATA_KEY,
    settings.SAMPLE_CLASS_METADATA_KEY,  # sampleClass
    settings.CMO_SAMPLE_CLASS_METADATA_KEY,  # sampleType::SMILE
    settings.LIBRARY_ID_METADATA_KEY,
    settings.BAITSET_METADATA_KEY,
    settings.PRESERVATION_METADATA_KEY,
    "sequencingCenter",
    "platform",
    "barcodeIndex",
    "flowCellId",
    "runMode",
    "runId",
]


def load_csv_to_global_dict(filepath):
    global POOLED_NORMALS  # contains table from assets/pooled_normals.csv
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_name = "_".join([row["bait_set"], row["preservation_type"], row["machine"], "POOLED_NORMAL"])
            sample_name = sample_name.upper()
            POOLED_NORMALS[sample_name] = row
            POOLED_NORMALS[sample_name]["pooled_normals_paths"] = (
                POOLED_NORMALS[sample_name]["pooled_normals_paths"].strip("{}").split(",")
            )


class SamplePooledNormal:
    def __init__(self, metadata):
        load_csv_to_global_dict(CSV_PATH)
        self.metadata = {k: metadata[k] for k in REQUIRED_KEYS if k in metadata}
        bait_set = metadata[settings.BAITSET_METADATA_KEY]
        preservation_type = metadata[settings.PRESERVATION_METADATA_KEY]
        machine = self.__get_machine__(metadata["runId"])
        sample_name = "_".join([bait_set, preservation_type, machine, "POOLED_NORMAL"])

        self.sample_name = sample_name
        self.pooled_normal = POOLED_NORMALS[sample_name]
        pooled_normals_paths = POOLED_NORMALS[sample_name]["pooled_normals_paths"]
        self.file_list = list()
        for p in pooled_normals_paths:
            f = FileRepository.filter(path=p).first()
            if "R1" in p:  # hacky
                f.metadata["R"] = "R1"
            else:
                f.metadata["R"] = "R2"
            self.file_list.append(f)

        # some overrides made because Pooled Normals don't contain these
        self.metadata[settings.REQUEST_ID_METADATA_KEY] = sample_name + "_REQID"
        self.metadata[settings.CMO_SAMPLE_TAG_METADATA_KEY] = sample_name
        self.metadata[settings.CMO_SAMPLE_NAME_METADATA_KEY] = sample_name
        self.metadata[settings.SAMPLE_ID_METADATA_KEY] = sample_name
        self.metadata["flowCellId"] = "PN_FCID"

        self.files_obj = FilesObj(self.file_list, "fastq")
        self.files = self.files_obj.get_files()

        self.sample_files = list()

        for r1_fastq in self.files["R1"]:
            self.metadata["barcodeIndex"] = spoof_barcode(r1_fastq)
            sample_file = SampleFile(r1_fastq, self.metadata)
            self.sample_files.append(sample_file)

        for r2_fastq in self.files["R2"]:
            self.metadata["barcodeIndex"] = spoof_barcode(r2_fastq)
            sample_file = SampleFile(r2_fastq, self.metadata)
            self.sample_files.append(sample_file)

    def __get_machine__(self, run_id):
        machine = run_id.split("_")[0]
        return machine

    def __repr__(self):
        sample_files_repr = "; ".join(repr(sample_file) for sample_file in self.sample_files)
        return f"SamplePooledNormal(Samples=[{sample_files_repr}])"
