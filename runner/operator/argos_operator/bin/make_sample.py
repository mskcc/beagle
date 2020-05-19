"""
This constructs a sample dictionary from the metadata in the Voyager/Beagle database
"""
import logging
import re

LOGGER = logging.getLogger(__name__)



def remove_with_caveats(samples):
    """
    Removes samples from a list of samples if they either
    don't contain a properly formatted patient ID or is
    'sampleNameMalformed', which happens when function
    format_sample_name returns it
    """
    data = list()
    error_data = list()
    for sample in samples:
        add = True
        sample_id = sample['sample_id']
        sample_name = sample['SM']
        patient_id = sample['patient_id']
        if sample_name == 'sampleNameMalformed':
            add = False
            LOGGER.info("Sample name is malformed for for %s; removing from set", sample_id)
        if patient_id[:2].lower() not in 'c-':
            add = False
            LOGGER.info(
                "Patient ID does not start with expected 'C-' prefix for %s; removing from set",
                sample_id)
        if add:
            data.append(sample)
        else:
            error_data.append(sample)

    return data, error_data


def format_sample_name(sample_name, specimen_type, ignore_sample_formatting=False):
    """
    Formats a given sample_name to legacy ARGOS naming conventions, provided that
    it is in valid CMO Sample Name format (see sample_pattern regex value, below)

    Current format is to prepend sample name with "s_" and convert all hyphens to
    underscores

    If it does not meet sample_pattern requirements OR is not a specimen_type=="CellLine",
    return 'sampleMalFormed'

    ignore_sample_formatting is applied if we want to return a sample name regardless of
    formatting
    """
    sample_pattern = re.compile(r'C-\w{6}-\w{4}-\w')

    if not ignore_sample_formatting:
        try:
            if "s_" in sample_name[:2]:
                return sample_name
            elif bool(sample_pattern.match(sample_name)) or "cellline" in specimen_type.lower():  # cmoSampleName is formatted properly
                sample_name = "s_" + sample_name.replace("-", "_")
                return sample_name
            LOGGER.error('Missing or malformed sampleName: %s', sample_name, exc_info=True)
            return 'sampleNameMalformed'
        except TypeError:
            LOGGER.error(
                "sampleNameError: sampleName is Nonetype; returning 'sampleNameMalformed'."
                )
            return "sampleNameMalformed"
    else:
        return sample_name


def check_samples(samples):
    """
    Makes sure the R1 and R2 pairing matches

    We are assuming the fastq data from the LIMS only differs in the 'R1'/'R2' string
    """
    for rg_id in samples:
        r1 = samples[rg_id]['R1']
        r2 = samples[rg_id]['R2']
        num_fastqs = len(r1)

        for index,fastq in enumerate(r1):
            expected_r2 = 'R2'.join(fastq.rsplit('R1', 1))
            if expected_r2 != r2[index]:
                LOGGER.error("Mismatched fastqs! Check data:")
                LOGGER.error("R1: %s" % fastq)
                LOGGER.error("Expected R2: %s" % expected_r2)
                LOGGER.error("Actual R2: %s" % r2[index])


def check_and_return_single_values(data):
    """
    data is a dictionary; each key contains a list of values.

    single_values are the expected keys that should contain only one value

    Concatenating pi and pi_email AND formatting the LB field are workarounds
    because some samples would have multiple values for these but the sample dict
    it returns must have one value only in order for the pipeline to execute
    """
    single_values = ['CN', 'PL', 'SM', 'bait_set', 'patient_id',
                     'species', 'tumor_type', 'sample_id', 'specimen_type',
                     'request_id']

    for key in single_values:
        value = set(data[key])
        if len(value) == 1:
            data[key] = value.pop()
        else:
            LOGGER.error("Expected only one value for %s!", key)
            LOGGER.error("Check import, something went wrong.")

    # concatenating pi and pi_email
    data['pi'] = '; '.join(set(data['pi']))
    data['pi_email'] = '; '.join(set(data['pi_email']))

    # hack; formats LB field so that it is a string
    library_id = [i for i in data['LB'] if i]
    number_of_library_ids = len(library_id)
    if number_of_library_ids > 0:
        data['LB'] = '_and_'.join(library_id)
    else:
        data['LB'] = data['SM'] + "_1"
    return data


def build_sample(data, ignore_sample_formatting=False):
    """
    Given some data - which is a list of samples originally from the LIMS, split up into one file
    per index - the data is then compiled into one sample dictionary consisting of one or more
    pairs of fastqs

    Note that ID and SM are different field values in ARGOS (RG_ID and ID, respectively, in ARGOS)
    but standardizing it here with what GATK sets bam headers to
    """

    sequencing_center = "MSKCC"
    platform = "Illumina"
    samples = dict()

    for value in data:
        meta = value['metadata']
        bid = value['id']
        request_id = meta['requestId']
        fpath = value['path']
        sample_id = meta['sampleId']
        library_id = meta['libraryId']
        bait_set = meta['baitSet']
        tumor_type = meta['tumorOrNormal']
        specimen_type = meta['specimenType']
        species = meta['species']
        cmo_sample_name = format_sample_name(meta['sampleName'], specimen_type, ignore_sample_formatting)
        if cmo_sample_name == "sampleNameMalformed":
            LOGGER.error("sampleName for %s is malformed", sample_id)
        flowcell_id = meta['flowCellId']
        barcode_index = meta['barcodeIndex']
        cmo_patient_id = meta['patientId']
        platform_unit = flowcell_id
        run_date = meta['runDate']
        r_orientation = meta['R']
        pi_name = meta['labHeadName']
        pi_email = meta['labHeadEmail']
        run_id = meta['runId']
        preservation_type = meta['preservation']
        rg_id = cmo_sample_name + "_1"
        if barcode_index:
            platform_unit = '_'.join([flowcell_id, barcode_index])
        try:
            rg_id = '_'.join([cmo_sample_name, platform_unit])
        except:
            LOGGER.info("RG ID couldn't be set.")
            LOGGER.info("Sample ID %s; patient ID %s", sample_id, cmo_patient_id)
            LOGGER.info("SampleName %s; platform unit %s", cmo_sample_name, platform_unit)
        if rg_id not in samples:
            samples[rg_id] = dict()
            sample = dict()
            sample['CN'] = (sequencing_center)
            sample['PL'] = (platform)
            sample['PU'] = (platform_unit)
            sample['LB'] = (library_id)
            sample['tumor_type'] = (tumor_type)
            sample['ID'] = (rg_id)
            sample['SM'] = (cmo_sample_name)
            sample['species'] = (species)
            sample['patient_id'] = cmo_patient_id
            sample['bait_set'] = bait_set
            sample['sample_id'] = sample_id
            sample['run_date'] = run_date
            sample['specimen_type'] = specimen_type
            sample['request_id'] = request_id
            sample['pi'] = pi_name
            sample['pi_email'] = pi_email
            sample['run_id'] = run_id
            sample['preservation_type'] = preservation_type
            sample['R1'] = list()
            sample['R1_bid'] = list()
            sample['R2'] = list()
            sample['R2_bid'] = list()
        else:
            sample = samples[rg_id]

        # fastq pairing assumes flowcell id + barcode index are unique per run
        if 'R1' in r_orientation:
            sample['R1'].append(fpath)
            sample['R1_bid'].append(bid)
        elif 'R2' in r_orientation:
            sample['R2'].append(fpath)
            sample['R2_bid'].append(bid)
        else:
            sample['bam'] = fpath
            sample['bam_bid'] = bid
        samples[rg_id] = sample
    check_samples(samples)

    result = dict()
    result['CN'] = list()
    result['PL'] = list()
    result['PU'] = list()
    result['LB'] = list()
    result['tumor_type'] = list()
    result['ID'] = list()
    result['SM'] = list()
    result['species'] = list()
    result['patient_id'] = list()
    result['bait_set'] = list()
    result['sample_id'] = list()
    result['run_date'] = list()
    result['specimen_type'] = list()
    result['R1'] = list()
    result['R2'] = list()
    result['R1_bid'] = list()
    result['R2_bid'] = list()
    result['bam'] = list()
    result['bam_bid'] = list()
    result['request_id'] = list()
    result['pi'] = list()
    result['pi_email'] = list()
    result['run_id'] = list()
    result['preservation_type'] = list()

    for rg_id in samples:
        sample = samples[rg_id]
        for key in sample:
            if 'R1' in key or 'R2' in key:
                for i in sample[key]:
                    result[key].append(i)
            else:
                result[key].append(sample[key])
    result = check_and_return_single_values(result)

    return result
