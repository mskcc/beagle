import sys
import os
import json
from .make_sample import is_cmo_sample_name_format


def create_pairing(data):
    pairing = ""
    for pair in data:
        normal = pair["normal_sample"]
        tumor = pair["tumor_sample"]
        if "noNormal" not in normal['sample_name']:
            pairing += "%s\t%s\n" % (normal["sample_name"], tumor["sample_name"])
    return pairing


def resolve_target(bait_set):
    target_assay = bait_set.lower()
    if "agilent" in target_assay:
        return "agilent"
    if "idt" in target_assay:
        return "idt"
    if "sureselect" in target_assay:
        return "agilent"
    return None


def create_mapping_string_from_sample(sample):
    mapping_string = ""
    sample_name = sample["sample_name"]
    target = resolve_target(sample["bait_set"])
    num_fastqs = len(sample["R1"])
    for i,fq in enumerate(sample["R1"]):
        r1 = fq["location"]
        r2 = sample["R2"][i]["location"]
        mapping_string += "%s\t%s\t%s\t%s\t%i\n" % (sample_name, target, r1, r2, num_fastqs)
    return mapping_string


def strip_values(data):
    for key in data:
        value = data[key]
        if isinstance(value, str):
            data[key] = value.strip()
    return data


def create_tempo_tracker_example(data):
    tracker = "CMO_Sample_ID\tMatching_normal\tCollaborator_ID_(or_DMP_Sample_ID)\tHistorical_Investigator_ID_(for_CCS_use)\tSample_Class_(T/N)\tBait_set_(Agilent/_IDT/WGS)\tIGO_Request_ID_(Project_ID)\t"
    key_order = [ "investigator_sample_id", "external_sample_id", "sample_class" ]
    key_order += [ "bait_set", "request_id" ]
    extra_keys = [ "tumor_type", "species", "recipe", "specimen_type", "sample_id" ]
    extra_keys += [ "investigator_name", "investigator_email", "pi", "pi_email", "patient_id", "preservation" ]
    extra_keys += [ "data_analyst", "data_analyst_email" ]
    for key in extra_keys:
        tracker += key + "\t"
    tracker = tracker.strip() + "\n"

    seen = set()

    for pair in data:
        normal = strip_values(pair["normal_sample"])
        tumor = strip_values(pair["tumor_sample"])

        running = list()
        running.append(tumor["sample_name"])
        running.append(normal["sample_name"])

        for key in key_order:
            running.append(tumor[key]) 
        for key in extra_keys:
            running.append(tumor[key])

        tracker += "\t".join(running) + "\n"

        if normal['sample_name'] not in seen:
            seen.add(normal['sample_name'])
            running_normal = list()
            running_normal.append(normal["sample_name"])
            running_normal.append("N/A")
            for key in key_order:
                running_normal.append(normal[key])
            for key in extra_keys:
                running_normal.append(normal[key])
            tracker += "\t".join(running_normal) + "\n"

    return tracker


def create_mapping(data):
    mapping_string = ""
    seen = set()
    for pair in data:
        normal = pair["normal_sample"]
        tumor = pair["tumor_sample"]
        normal_map = create_mapping_string_from_sample(normal)
        tumor_map = create_mapping_string_from_sample(tumor)
        mapping_string += tumor_map
        if normal['sample_name'] not in seen:
            mapping_string += normal_map
        seen.add(normal['sample_name'])
    return mapping_string


if __name__ == "__main__":
    flist = open(sys.argv[1], "r")
    
    data = list() 
    for filename in flist:
        f = open(filename.strip(), 'r')
        data_temp = json.load(f)
        data = data + data_temp

    pairing = create_pairing(data)
    mapping = create_mapping(data)
    tracker = create_tempo_tracker_example(data)

    open('pairing.txt', 'w').write(pairing)
    open('mapping.txt', 'w').write(mapping)
    open('tracker.txt', 'w').write(tracker)
