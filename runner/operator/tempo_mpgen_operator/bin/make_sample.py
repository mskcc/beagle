import logging
import re
logger = logging.getLogger(__name__)


def remove_with_caveats(samples):
    data = list()
    error_data = list()
    for sample in samples:
        add = True
        igo_id = sample['sample_id']
        sample_name = sample['sample_name']
        patient_id = sample['patient_id']
        if sample_name == "emptySampleName":
            add = False
        if sample_name == "nullSampleName":
            add = False
        if add:
            data.append(sample)
        else:
            error_data.append(sample)
    return data, error_data


def format_sample_name(sample_name):
    sample_pattern = re.compile(r'C-\w{6}-\w{4}-\w')
    try:
        if "s_" in sample_name[:2]:
            return sample_name
        elif bool(sample_pattern.match(sample_name)):  # cmoSampleName is formatted properly
            sample_name = "s_" + sample_name.replace("-", "_")
            return sample_name
        elif not sample_name:
            return "emptySampleName"
        else:
            logging.error('Missing or malformed sampleName: %s' % sample_name, exc_info=True)
            return sample_name
    except TypeError as error:
        logger.error("sampleNameError: sampleName is Nonetype; returning 'sampleNameMalformed'.")
        return "nullSampleName"


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
    single_values = [ 'sequencing_center', 'platform', 'sample_name',
                    'bait_set', 'patient_id', 'species', 'tumor_type',
                    'sample_id', 'specimen_type', 'external_sample_id', 
                    'investigator_sample_id', 'investigator_name', 'investigator_email',
                    'preservation', 'sample_class', 'recipe', 'request_id',
                    'data_analyst', 'data_analyst_email' ]

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

    data['platform_unit'] = '_'.join(set(data['platform_unit']))

    # hack; formats LB field so that it is a string
    lb = [i for i in data['library'] if i ]
    if len(lb) > 0:
        data['library'] = '_and_'.join(lb)
    else:
        data['library'] = ""
    return data


# TODO: if data is not from the LIMS, these hardcoded values will need to be generalized
def build_sample(data):
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
        cmo_sample_name = format_sample_name(meta['sampleName'])
        flowcell_id = meta['flowCellId']
        barcode_index = meta['barcodeIndex']
        cmo_patient_id = meta['patientId']
        pu = flowcell_id
        if not pu:
            pu = "FAKEFLOWCELL"
        run_date = meta['runDate']
        r_orientation = meta['R']
        pi = meta['labHeadName']
        pi_email = meta['labHeadEmail']
        external_sample_id = meta['externalSampleId']
        investigator_name = meta['investigatorName']
        investigator_email = meta['investigatorEmail']
        investigator_sample_id = meta['investigatorSampleId']
        preservation = meta['preservation']
        sample_class = meta['sampleClass']
        recipe = meta['recipe']
        data_analyst = meta['dataAnalystName']
        data_analyst_email = meta['dataAnalystEmail']
        if barcode_index:
            pu = '_'.join([flowcell_id,  barcode_index])
        rg_id = cmo_patient_id + "_RGID_1"
        if cmo_sample_name and pu:
            rg_id = '_'.join([cmo_sample_name, pu])
        if rg_id not in samples:
            samples[rg_id] = dict()
            sample = dict()
            sample['sequencing_center'] = (CN)
            sample['platform'] = (PL)
            sample['platform_unit'] = (pu)
            sample['library'] = (lb)
            sample['tumor_type'] = (tumor_type)
            sample['read_group_id'] = (rg_id)
            sample['sample_name'] = (cmo_sample_name)
            sample['species'] = (species)
            sample['patient_id'] = cmo_patient_id
            sample['bait_set'] = bait_set
            sample['sample_id'] = igo_id
            sample['run_date'] = run_date
            sample['specimen_type'] = specimen_type
            sample['request_id'] = request_id
            sample['pi'] = pi
            sample['pi_email'] = pi_email
            sample['external_sample_id'] = external_sample_id
            sample['investigator_sample_id'] = investigator_sample_id
            sample['investigator_name'] = investigator_name
            sample['investigator_email'] = investigator_email
            sample['preservation'] = preservation
            sample['sample_class'] = sample_class
            sample['recipe'] = recipe
            sample['data_analyst'] = data_analyst
            sample['data_analyst_email'] = data_analyst_email
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
    result['sequencing_center'] = list()
    result['platform'] = list()
    result['platform_unit'] = list()
    result['library'] = list()
    result['tumor_type'] = list()
    result['read_group_id'] = list()
    result['sample_name'] = list()
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
    result['request_id'] = list()
    result['pi'] = list()
    result['pi_email'] = list()
    result['external_sample_id'] = list()
    result['investigator_sample_id'] = list()
    result['investigator_name'] = list()
    result['investigator_email'] = list()
    result['preservation'] = list()
    result['sample_class'] = list()
    result['recipe'] = list()
    result['data_analyst'] = list()
    result['data_analyst_email'] = list()

    for rg_id in samples:
        sample = samples[rg_id]
        for key in sample:
            result[key].append(sample[key])
    result = check_and_return_single_values(result)

    return result
