import logging
import re
logger = logging.getLogger(__name__)


def remove_with_caveats(samples):
    data = list()
    error_data = list()
    for sample in samples:
        add = True
        igo_id = sample['igo_id']
        sample_name = sample['SM']
        patient_id = sample['patient_id']
        if sample_name == 'sampleNameMalformed':
            add = False
            logging.debug("Sample name is malformed for for %s; removing from set" % igo_id)
        if patient_id[:2].lower() not in 'c-':
            add = False
            logging.debug("Patient ID does not start with expected 'C-' prefix for %s; removing from set" % igo_id)
        if add:
            data.append(sample)
        else:
            error_data.append(sample)

    return data, error_data


def format_sample_name(sample_name, ignore_sample_formatting=False):
    sample_pattern = re.compile(r'C-\w{6}-\w{4}-\w')

    if not ignore_sample_formatting:
        try:
            if "s_" in sample_name[:2]:
                return sample_name
            elif bool(sample_pattern.match(sample_name)):  # cmoSampleName is formatted properly
                sample_name = "s_" + sample_name.replace("-", "_")
                return sample_name
            else:
                logging.error('Missing or malformed sampleName: %s' % sample_name, exc_info=True)
                return 'sampleNameMalformed'
        except TypeError as error:
            logger.error("sampleNameError: sampleName is Nonetype; returning 'sampleNameMalformed'.")
            return "sampleNameMalformed"
    else:
        return sample_name


def check_samples(samples):
    for rg_id in samples:
        r1 = samples[rg_id]['R1']
        r2 = samples[rg_id]['R2']

        expected_r2 = 'R2'.join(r1.rsplit('R1', 1))
        if expected_r2 != r2:
            logging.error("Mismatched fastqs! Check data:")
            logging.error("R1: %s" % r1)
            logging.error("Expected R2: %s" % expected_r2)
            logging.error("Actual R2: %s" % r2)


def check_and_return_single_values(data):
    single_values = [ 'CN', 'PL', 'SM', 'bait_set', 'patient_id', 'species', 'tumor_type', 'igo_id', 'specimen_type', 'run_id', 'preservation_type' ]

    for key in single_values:
        value = set(data[key])
        if len(value) == 1:
            data[key] = value.pop()
        else:
            logging.error("Expected only one value for %s!" %key)
            logging.error("Check import, something went wrong.")

    # concatenating pi and pi_email
    data['pi'] = '; '.join(set(data['pi']))
    data['pi_email'] = '; '.join(set(data['pi_email']))

    # hack; formats LB field so that it is a string
    lb = [i for i in data['LB'] if i ]
    if len(lb) > 0:
        data['LB'] = '_and_'.join(lb)
    else:
        data['LB'] = ""
    return data


# TODO: if data is not from the LIMS, these hardcoded values will need to be generalized
def build_sample(data, ignore_sample_formatting=False):
    # note that ID and SM are different field values in ROSLIN (RG_ID and ID, respectively, in ROSLIN)
    # but standardizing it here with what GATK sets bam headers to

    CN = "MSKCC"
    PL = "Illumina"
    samples = dict()

    for i,v in enumerate(data):
        meta = v['metadata']
        bid = v['id']
        request_id = meta['requestId']
        fpath = v['path']
        fname = v['file_name']
        igo_id = meta['sampleId']
        lb = meta['libraryId']
        bait_set = meta['baitSet']
        tumor_type = meta['tumorOrNormal']
        specimen_type = meta['specimenType']
        species = meta['species']
        cmo_sample_name = format_sample_name(meta['sampleName'], ignore_sample_formatting)
        flowcell_id = meta['flowCellId']
        barcode_index = meta['barcodeIndex']
        cmo_patient_id = meta['patientId']
        pu = flowcell_id
        run_date = meta['runDate']
        r_orientation = meta['R']
        pi = meta['labHeadName']
        pi_email = meta['labHeadEmail']
        run_id = meta['runId']
        preservation_type = meta['preservation']
        if barcode_index:
            pu = '_'.join([flowcell_id,  barcode_index])
        rg_id = '_'.join([cmo_sample_name, pu])
        if rg_id not in samples:
            samples[rg_id] = dict()
            sample = dict()
            sample['CN'] = (CN)
            sample['PL'] = (PL)
            sample['PU'] = (pu)
            sample['LB'] = (lb)
            sample['tumor_type'] = (tumor_type)
            sample['ID'] = (rg_id)
            sample['SM'] = (cmo_sample_name)
            sample['species'] = (species)
            sample['patient_id'] = cmo_patient_id
            sample['bait_set'] = bait_set
            sample['igo_id'] = igo_id
            sample['run_date'] = run_date
            sample['specimen_type'] = specimen_type
            sample['request_id'] = request_id
            sample['pi'] = pi
            sample['pi_email'] = pi_email
            sample['run_id'] = run_id
            sample['preservation_type'] = preservation_type
        else:
            sample = samples[rg_id]

        # fastq pairing assumes flowcell id + barcode index are unique per run
        if 'R1' in r_orientation:
            sample['R1'] = fpath
            sample['R1_bid'] = bid
        else:
            sample['R2'] = fpath
            sample['R2_bid'] = bid
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
    result['igo_id'] = list() 
    result['run_date'] = list()
    result['specimen_type'] = list()
    result['R1'] = list()
    result['R2'] = list()
    result['R1_bid'] = list()
    result['R2_bid'] = list()
    result['request_id'] = list()
    result['pi'] = list()
    result['pi_email'] = list()
    result['run_id'] = list()
    result['preservation_type'] = list()

    for rg_id in samples:
        sample = samples[rg_id]
        for key in sample:
            result[key].append(sample[key])
    result = check_and_return_single_values(result)

    return result
