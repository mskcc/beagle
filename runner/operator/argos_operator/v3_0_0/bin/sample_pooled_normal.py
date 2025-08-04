import csv
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CSV_PATH = PROJECT_ROOT / "assets" / "pooled_normals.csv"
POOLED_NORMALS = {}


def load_csv_to_global_dict(filepath):
    global POOLED_NORMALS
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_name = "_".join([row["bait_set"], row["preservation_type"], row["machine"], "POOLED_NORMAL"])
            POOLED_NORMALS[sample_name] = row


class SamplePooledNormal:
    def __init__(self):
        print(CSV_PATH)
        from pprint import pprint

        load_csv_to_global_dict(CSV_PATH)

        pprint(POOLED_NORMALS)
