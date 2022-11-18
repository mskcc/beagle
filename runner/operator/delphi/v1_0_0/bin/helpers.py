import csv


def get_data_from_file(input_csv):
    data = list()
    with open(input_csv, "r") as f:
        read_csv = csv.DictReader(f, delimiter=",") 
        header = read_csv.fieldnames
        for row in read_csv:
            data.append(row)
    return header, data

def construct_delphi_input_jsons(header,data):
    input_jsons = ""
    return input_jsons
