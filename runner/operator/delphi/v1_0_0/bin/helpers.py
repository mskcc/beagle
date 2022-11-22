import csv


def get_data_from_file(input_csv):
    data = list()
    with open(input_csv, "r") as f:
        read_csv = csv.DictReader(f, delimiter=",")
        header = read_csv.fieldnames
        for row in read_csv:
            data.append(row)
    return header, data


def construct_delphi_input_jsons(header, data):
    inputs = dict()
    inputs["somatic"] = True
    inputs["name"] = "Delphi A Tempo/Chronos Run"
    inputs["app"] = ""
    inputs["tags"] = dict()
    inputs["output_metadata"] = dict()
    inputs["output_directory"] = "/juno/work/ci/ops/delphiA"
    inputs["mapping"] = list()
    for row in data:
        current_sample = dict()
        current_sample["assay"] = "exome"
        current_sample["target"] = "impact505"
        current_sample["sample"] = row["sample"]
        current_sample["fastq_pe1"] = {"class": "File", "location": row["R1"]}
        current_sample["fastq_pe2"] = {"class": "File", "location": row["R2"]}
        inputs["mapping"].append(current_sample)
    input_jsons = dict()
    input_jsons["inputs"] = inputs
    return input_jsons
