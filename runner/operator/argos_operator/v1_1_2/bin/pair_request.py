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
from .retrieve_samples_by_query import get_samples_from_patient_id, get_pooled_normals, get_dmp_bam
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


def compile_pairs(samples, pairing_info=None):
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
        if pairing_info:
            """
            Creating samples, based on predefined pairing list
            """
            for pair in pairing_info['pairs']:
                tumor_sample = pair['tumor']
                if tumor['SM'] == tumor_sample['sample_id']:
                    for normal in normals:
                        normal_sample = pair['normal']
                        if 'poolednormal' in normal_sample['sample_id'].lower():
                            """
                            We should have a pool normal to pair with here
                            """
                            normal_run_ids = normal['run_id']
                            normal_bait_set = normal['bait_set']
                            normal_preservation = [x.lower() for x in normal['preservation_type']]
                            if all(elem in normal_run_ids for elem in tumor['run_id']):
                                """
                                Checks if any of the run ids in the pre-created normal samples
                                are also all in the tumor sample
                                """
                                if normal_bait_set.lower() in tumor['bait_set'].lower():
                                    tumor_preservations = [x.lower() for x in tumor['preservation_type']]
                                    # Must check if FFPE or other
                                    if 'ffpe' in normal_preservation:
                                        if 'ffpe' in tumor_preservations:
                                            pairs['tumor'].append(tumor)
                                            pairs['normal'].append(normal)
                                            break
                                    else:
                                        if 'ffpe' not in tumor_preservations:
                                            pairs['tumor'].append(tumor)
                                            pairs['normal'].append(normal)
                                            break
                        elif normal['SM'] == normal_sample['sample_id']:
                            """
                            This pairs with a dmp normal
                            """
                            pairs['tumor'].append(tumor)
                            pairs['normal'].append(normal)
                            break
        else:
            from pprint import pprint
            print("Pairing tumor below...")
            pprint(tumor)
            patient_id = tumor['patient_id']
            if patient_id:
                bait_set = tumor['bait_set']
                run_ids = tumor['run_id']
                preservation_types = tumor['preservation_type']
                normal = get_viable_normal(normals, patient_id, bait_set)
                if normal:
                    LOGGER.info("Pairing %s (%s) with %s (%s)",
                                tumor['sample_id'],
                                tumor['SM'],
                                normal['sample_id'],
                                normal['SM'])
                    pairs['tumor'].append(tumor)
                    pairs['normal'].append(normal)
                else:
                    LOGGER.info("Missing normal for sample %s (%s); querying patient %s",
                                tumor['sample_id'],
                                tumor['SM'],
                                patient_id)
                    patient_samples = get_samples_from_patient_id(patient_id)
                    new_normals = get_by_tumor_type(patient_samples, "Normal")
                    new_normal = get_viable_normal(new_normals, patient_id, bait_set)
                    if new_normal:
                        LOGGER.info("Pairing %s (%s) with %s (%s)",
                                    tumor['sample_id'],
                                    tumor['SM'],
                                    new_normal['sample_id'],
                                    new_normal['SM'])
                        pairs['tumor'].append(tumor)
                        pairs['normal'].append(new_normal)
                    else:
                        LOGGER.info("No normal found for patient %s; checking for DMP Normal", patient_id)
                        dmp_normal = get_dmp_bam(patient_id, bait_set, "Normal")
                        if dmp_normal:
                            LOGGER.info("Pairing %s (%s) with %s (%s)",
                                        tumor['sample_id'],
                                        tumor['SM'],
                                        dmp_normal['sample_id'],
                                        dmp_normal['SM'])
                            pairs['tumor'].append(tumor)
                            pairs['normal'].append(dmp_normal)
                        else:
                            pooled_normal = get_pooled_normals(run_ids, preservation_types, bait_set)
                            LOGGER.info("No DMP Normal found for patient %s; checking for Pooled Normal",
                                        patient_id)
                            if pooled_normal:
                                LOGGER.info("Pairing %s (%s) with %s (%s)",
                                            tumor['sample_id'],
                                            tumor['SM'],
                                            pooled_normal['sample_id'],
                                            pooled_normal['SM'])
                                pairs['tumor'].append(tumor)
                                pairs['normal'].append(pooled_normal)
                            else:
                                LOGGER.error("No normal found for %s (%s), patient %s",
                                             tumor['sample_id'],
                                             tumor['SM'],
                                             patient_id)
            else:
                LOGGER.error("NoPatientIdError: No patient_id found for %s (%s); skipping.",
                             tumor['sample_id'],
                             tumor['SM'])
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
