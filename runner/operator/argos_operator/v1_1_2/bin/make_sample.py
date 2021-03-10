"""
This constructs a sample dictionary from the metadata in the Voyager/Beagle database
"""
import logging
import os
import re
from runner.operator.helper import format_sample_name, get_r_orientation, spoof_barcode
from file_system.repository.file_repository import FileRepository
from pprint import pprint

LOGGER = logging.getLogger(__name__)


def remove_with_caveats(samples):
    """
    Removes samples from a list of samples if they either
    don't contain a 'sampleNameMalformed', which happens when function
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
        if not patient_id:
            add = False
            LOGGER.info("No patient ID for sample %s; removing from set", sample_id)
        elif isinstance(patient_id, str):
            if not patient_id.strip():
                add = False
                LOGGER.info("Empty string for patient ID in sample %s; removing from set", sample_id)
        if add:
            data.append(sample)
        else:
            error_data.append(sample)
    return data, error_data


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


    # run_ids need to be one list
    run_ids = data['run_id']
    if any(isinstance(run_id, list) for run_id in run_ids):
        run_ids = [item for sublist in run_ids for item in sublist]
        data['run_id'] = list(set(run_ids))
    return data


def get_file(fpath):
    files = FileRepository.all()
    data = FileRepository.filter(queryset=files, path=fpath)
    if data:
        return data[0]
    return None

def build_sample(data, ignore_sample_formatting=False):
    """
    Given some data - which is a list of samples originally from the LIMS, split up into one file
    per index - the data is then compiled into one sample dictionary consisting of one or more
    pairs of fastqs

    Note that ID and SM are different field values in ARGOS (RG_ID and ID, respectively, in ARGOS)
    but standardizing it here with what GATK sets bam headers to
    """

    samples = dict()

    for value in data:
        fpath = value['path']
        curr_file = get_file(fpath)
        meta = value['metadata']
        bid = value['id']
        sequencing_center = meta['sequencingCenter']
        platform = meta['platform']
        request_id = meta['requestId']
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
        if sample_id not in samples:
            samples[sample_id] = dict()
            sample = dict()
            sample['CN'] = (sequencing_center)
            sample['PL'] = (platform)
            sample['PU'] = list()
            sample['LB'] = (library_id)
            sample['tumor_type'] = (tumor_type)
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
            sample['ID'] = list()
            sample['R1'] = list()
            sample['R1_bid'] = list()
            sample['R2'] = list()
            sample['R2_bid'] = list()
            sample['fastqs'] = list()
        else:
            sample = samples[sample_id]

        # Queueing up fastqs for pairing later; RG ID and PU
        # will be assigned based on Fastqs object
        if 'R1' in r_orientation or 'R2' in r_orientation:
            sample['fastqs'].append(curr_file)
        else:
        # DMP bams found; assigning RG ID and PU here
        # There will always be only one DMP bam, so assign explicitly
            sample['bam'] = fpath
            sample['bam_bid'] = bid
            sample['PU'] = (platform_unit)
            sample['ID'] = (rg_id)
        samples[sample_id] = sample

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

    for sample_id in samples:
        sample = samples[sample_id]
        for key in sample:
            if key == 'fastqs':
                if sample['fastqs']:
                    fastqs = Fastqs(sample['SM'],sample['fastqs'])
                    result['R1'] = fastqs.r1
                    result['R1_bid'] = fastqs.r1_bids
                    result['R2'] = fastqs.r2
                    result['R2_bid'] = fastqs.r2_bids
                    result['PU'] = fastqs.pu
                    result['ID'] = fastqs.rg_id
            else:
                result[key].append(sample[key])
#    pprint(result)
    result = check_and_return_single_values(result)
#    pprint(set(result['PU']))
    return result


class Fastqs:
    """
    Fastqs class to hold pairs of fastqs

    Does the pairing from a list of files

    The paired bool is True if all of the R1s in file list find a matching R2
    """
    def __init__(self, sample_name, file_list):
        self.sample_name = sample_name
        self.fastqs = dict()
        self.r1 = list()
        self.r2 = list()
        self.r2_bids = list()
        self.paired = True
        self._set_R(file_list)
        self.r1_bids = self._set_bids(self.r1)
        self.r2_bids = self._set_bids(self.r2)
        self.pu = self._set_pu()
        self.rg_id = self._set_rg_id()


    def _set_bids(self, r):
        r_bids = list()
        for f in r:
            r_file = get_file(f)
            r_bids.append(r_file.id)
        return r_bids


    def _set_pu(self):
        """
        Creating a list of PU values; used by argos pipeline as scatter input

        Only iterating across r1s since r1 and r2 should have the same metadata
        """
        pu = list()
        for f in self.r1:
            metadata = get_file(f).metadata
            if 'poolednormal' in self.sample_name.lower():
                flowcell_id = 'PN_FCID'
                r = get_r_orientation(f)
                barcode_index = spoof_barcode(os.path.basename(f),r)
            else:
                flowcell_id = metadata['flowCellId']
                barcode_index = metadata['barcodeIndex']
            platform_unit = flowcell_id
            if barcode_index:
                platform_unit = '_'.join([flowcell_id, barcode_index])
            pu.append(platform_unit)
        return pu


    def _set_rg_id(self):
        """
        Creating a list of RG_ID values; used by argos pipeline as scatter input

        Only iterating across r1s since r1 and r2 should have the same metadata
        """
        rg_ids = list()
        for i,f in enumerate(self.r1):
            metadata = get_file(f).metadata
            sample_name = self.sample_name
            pu = self.pu[i]
            rg_id = '_'.join([sample_name, pu])
            rg_ids.append(rg_id)
        return rg_ids


    def _set_R(self, file_list):
        """
        From the file list, retrieve R1 and R2 fastq files

        Sets PU and bids, as well

        Uses _get_fastq_from_list() to find R2 pair.
        """
        r1s = list()
        r2s = list()
        for i in file_list:
            f = i.file
            r = get_r_orientation(f.path)
            if r == "R1":
                r1s.append(f)
            if r == "R2":
                r2s.append(f)
        for f in r1s:
            self.r1.append(f.path)
            fastq1 = f.path
            expected_r2 = 'R2'.join(fastq1.rsplit('R1', 1))
            fastq2 = self._get_fastq_from_list(expected_r2, r2s)
            if fastq2:
                self.r2.append(fastq2.path)
            else:
                print("No fastq R2 found for %s" % f.path)
                self.paired = False


    def __str__(self):
        s = "R1:\n"
        for i in self.r1:
            s += i.path +"\n"
        s += "\nR2:\n"
        for i in self.r2:
            s += i.path + "\n"
        return s


    def _get_fastq_from_list(self, fastq_path, fastq_files):
        """
        Given fastq_path, find it in the list of fastq_files and return
        that File object
        """
        for f in fastq_files:
            fpath = f.path
            if fastq_path == fpath:
                return f
