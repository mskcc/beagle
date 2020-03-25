"""
Given a request, this module will attempt to find a pair for every tumor within that request.

It performs the following:

  - Checks if a normal exists within that same request
  - Checks if a normal exists in a different request for that same patient
  - Checks if a DMP bam will be within that request (unimplemented as of 2020-03-03; upcoming)
  - Checks if a pooled normal exists

Normals will have to have the same patient and bait set in order to be considered "viable"
"""
import logging
from datetime import datetime as dt
from .retrieve_samples_by_query import get_samples_from_patient_id, get_pooled_normals
LOGGER = logging.getLogger(__name__)


def get_by_tumor_type(data, tumor_type):
    """
    Retrieves a set of samples that contain a value tumor_type

    tumor_tupe is typically Normal or Tumor
    """
    samples = list()
    for sample in data:
        if tumor_type.lower() in sample['tumor_type'].lower():
            samples.append(sample)
    return samples


def compare_dates(normal, viable_normal, date_string):
    """
    Compares dates between two normals; returns the most recent
    """
    for run_date in normal['run_date']:
        normal_date = dt.strptime(run_date, date_string)
        for vrun_date in viable_normal['run_date']:
            vnormal_date = dt.strptime(vrun_date, date_string)
            if vnormal_date < normal_date:
                viable_normal = normal
    return viable_normal


def get_viable_normal(normals, patient_id, bait_set):
    """
    From a set of normals, return the ones that have matching patient_id, bait_set,
    and the most recent

    Does not check for Pooled Normals; that's done separately
    """
    viable_normal = dict()
    for normal in normals:
        if normal['patient_id'] == patient_id and normal['bait_set'] == bait_set:
            if viable_normal:
                try:
                    viable_normal = compare_dates(normal, viable_normal, '%y-%m-%d')
                except ValueError:
                    LOGGER.debug("Trying different date parser")
                    viable_normal = compare_dates(normal, viable_normal, '%Y-%m-%d')
            else:
                viable_normal = normal
    return viable_normal


def compile_pairs(samples):
    """
    Creates pairs of tumors and normals from a list of samples
    """
    tumors = get_by_tumor_type(samples, "Tumor")
    normals = get_by_tumor_type(samples, "Normal")

    # pairing
    pairs = dict()
    pairs['tumor'] = list()
    pairs['normal'] = list()

    num_tumors = len(tumors)
    if num_tumors == 0:
        LOGGER.error("No tumor samples found; pairing will not be performed.")
        LOGGER.error("Returning an empty list of pairs.")

    for tumor in tumors:
        LOGGER.info("Pairing tumor sample %s", tumor['sample_id'])
        patient_id = tumor['patient_id']
        if patient_id:
            bait_set = tumor['bait_set']
            run_ids = tumor['run_id']
            preservation_types = tumor['preservation_type']
            normal = get_viable_normal(normals, patient_id, bait_set)
            if normal:
                LOGGER.info("Pairing %s with %s", tumor['sample_id'], normal['sample_id'])
                pairs['tumor'].append(tumor)
                pairs['normal'].append(normal)
            else:
                LOGGER.info("Missing normal for sample %s; querying patient %s", tumor['sample_id'], patient_id)
                patient_samples = get_samples_from_patient_id(patient_id)
                new_normals = get_by_tumor_type(patient_samples, "Normal")
                new_normal = get_viable_normal(new_normals, patient_id, bait_set)
                if new_normal:
                    LOGGER.info("Pairing %s with %s", tumor['sample_id'], new_normal['sample_id'])
                    pairs['tumor'].append(tumor)
                    pairs['normal'].append(new_normal)
                else:
                    pooled_normal = get_pooled_normals(run_ids, preservation_types, bait_set)
                    LOGGER.info("No normal found for patient %s; checking for Pooled Normal", patient_id)
                    if pooled_normal:
                        LOGGER.info("Pairing %s with %s", tumor['sample_id'], pooled_normal['sample_id'])
                        pairs['tumor'].append(tumor)
                        pairs['normal'].append(pooled_normal)
                    else:
                        LOGGER.error("No normal found for %s, patient %s", tumor['sample_id'], patient_id)
        else:
            LOGGER.error("NoPatientIdError: No patient_id found for %s; skipping.", tumor['sample_id'])
    return pairs


def create_pairing_info(pairs):
    """
    Outputs pairing data in the form of TUMOR\tNORMAL
    Used in legacy Tempo and Roslin
    """
    output_string = ""
    num_tumors = len(pairs['tumor'])
    for i in range(0, num_tumors):
        tumor_name = pairs['tumor'][i]['SM']
        normal_name = pairs['normal'][i]['SM']
        output_string += "\t".join([normal_name, tumor_name]) + "\n"
    return output_string
