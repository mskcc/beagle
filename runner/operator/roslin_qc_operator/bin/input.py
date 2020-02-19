"""
Module for generating input dataset for use with Roslin QC operator

Example input datastructure format:

db_files:
    fp_genotypes: db_files['value']['fp_genotypes']
    hotspot_list_maf: db_files['value']['hotspot_list_maf']
    conpair_markers: db_files['value']['conpair_markers']
runparams:
    project_prefix: runparams['value']['project_prefix']
    genome: runparams['value']['genome']
    scripts_bin: runparams['value']['scripts_bin']
    assay: ---MISSING---
    pi: ---MISSING---
    pi_email: ---MISSING---
ref_fasta: ref_fasta
clstats1: [clstats1]
clstats2: [clstats2]
md_metrics: [md_metrics]
hs_metrics: [hs_metrics]
insert_metrics: [insert_metrics]
per_target_coverage: [per_target_coverage]
qual_metrics: [qual_metrics]
doc_basecounts: [doc_basecounts]
conpair_pileups: [conpair_pileups]
pairs: [pair]
"""
import json
import urllib
from file_system.models import FileMetadata, File
from runner.models import Port
import urllib.parse

def build_sample(filemetadata_instance, company_name = "MSKCC", platform = "Illumina"):
    """
    Create base Roslin CWL sample datastructure from the FileMetadata
    """
    sample = {}
    sample['CN'] = company_name
    sample['PL'] = platform
    sample['PU'] =  filemetadata_instance.metadata['flowCellId']
    sample['LB'] = filemetadata_instance.metadata['libraryId']
    sample['tumor_type'] = filemetadata_instance.metadata['tumorOrNormal']
    sample['ID'] = '_'.join([filemetadata_instance.metadata['sampleName'], filemetadata_instance.metadata['flowCellId']])
    sample['SM'] = filemetadata_instance.metadata['sampleName']
    sample['species'] = filemetadata_instance.metadata['species']
    sample['patient_id'] = filemetadata_instance.metadata['patientId']
    sample['bait_set'] = filemetadata_instance.metadata['baitSet']
    sample['igo_id'] = filemetadata_instance.metadata['sampleId']
    sample['run_date'] = filemetadata_instance.metadata['runDate']
    sample['specimen_type'] = filemetadata_instance.metadata['specimenType']
    sample['request_id'] = filemetadata_instance.metadata['requestId']
    return(sample)

def file_to_cwl(file_instance):
    """
    Convert a Beagle File instance into a dict in CWL File format dict

    example:
    {'class': 'File', 'path': '/path/to/foo.txt'}
    """
    d = {
    'class': 'File',
    'path': file_instance.path
    }
    return(d)

def path_to_cwl(filepath):
    """
    Convert a filepath string into a CWL File format dict
    """
    d = {
    'class': 'File',
    'path': filepath
    }
    return(d)

def get_assay_from_run(run_instance):
    """
    Return the assay from a Run instance
    This is a hold-over method until Run instance db model gets updated; update this later
    """
    return(run_instance.output_metadata['assay'])

def create_files_data_from_ports_with_names(ports):
    """
    Retrieve the File entries for each Port entry, while keeping the associated Port.name attribute
    """
    # list of dicts for File and 'name'
    # TODO: use a Django query instead of iteration
    files = []
    for port in ports:
        # arbitrary ordering to force a test-able output
        for file in port.files.all().order_by('path'):
            file_cwl = file_to_cwl(file)
            d = { 'name': port.name, 'file': file_cwl }
            files.append(d)
    return(files)

def parse_pairs_from_ports(ports_queryset):
    """
    Search the set of Ports for "pair" entries and format them into a list of tumor normal pair entries
    """
    pair_ports = ports_queryset.filter(name = "pair")
    pairs = []

    # get the tumor and normal R1 and R2 items from FileMetadata assocaited with File's associated with each Port
    all_pair_items = []
    for port in pair_ports:
        pair_items = []
        # all the Files assocaited with a Port
        files = port.files.all()
        for file in files:
            # get the highest 'version' number FileMetadata instance for the File
            filemetata_instance = FileMetadata.objects.filter(file = file).order_by('-version').first()
            R1_or_R2 = filemetata_instance.metadata['R']
            tumor_or_normal = filemetata_instance.metadata['tumorOrNormal']
            pair_items.append( {'filemetadata': filemetata_instance, 'R1_or_R2': R1_or_R2, 'tumor_or_normal': tumor_or_normal  } )
        all_pair_items.append(pair_items)

    # parse the entries into a sensible mapping of tumor and normal R1 and R2
    for pair_items in all_pair_items:
        pair_set = {}
        pair_set['tumor'] = {}
        pair_set['normal'] = {}
        # TODO: how to handle case where wrong number of items are associated? Should be 1 of each tumor/normal + R1/R2
        for item in pair_items:
            if item['tumor_or_normal'] == 'Tumor' and item['R1_or_R2'] == 'R1':
                pair_set['tumor']['R1'] = item['filemetadata']
            elif item['tumor_or_normal'] == 'Tumor' and item['R1_or_R2'] == 'R2':
                pair_set['tumor']['R2'] = item['filemetadata']
            elif item['tumor_or_normal'] == 'Normal' and item['R1_or_R2'] == 'R1':
                pair_set['normal']['R1'] = item['filemetadata']
            elif item['tumor_or_normal'] == 'Normal' and item['R1_or_R2'] == 'R2':
                pair_set['normal']['R2'] = item['filemetadata']
        pairs.append(pair_set)
    return(pairs)

def parse_bams_from_ports(ports_queryset):
    """
    Search a set of Ports for the 'bams' entries and format them into a list of tumor normal pair entries
    """
    bam_ports = ports_queryset.filter(name = "bams")
    bams = []
    for bam in bam_ports:
        # get the Beagle database id for each bam file out of the `db_value` field`
        # TODO: need to refactor this to get it from the Port.files association; right now that association lacks the tumor/normal information needed to know which bam is which
        files_data = bam.db_value
        tumor_bam_data = files_data[0]
        tumor_bam_bid = urllib.parse.urlsplit(tumor_bam_data['location']).netloc
        tumor_bam_file_instance = File.objects.get(id = tumor_bam_bid)
        normal_bam_data = files_data[1]
        normal_bam_bid = urllib.parse.urlsplit(normal_bam_data['location']).netloc
        normal_bam_file_instance = File.objects.get(id = normal_bam_bid)
        bams.append([tumor_bam_file_instance, normal_bam_file_instance])
    return(bams)

def pair_to_cwl(pair):
    """
    Convert a single tumor normal pair dict to CWL format datastructure

    pair = {
        'normal': {
            'R1': FileMetadata,
            'R2': FileMetadata
        },
        'tumor': {
            'R1': FileMetadata,
            'R2': FileMetadata
        }
    """
    # get the base datastructure dict for each R1 and R2
    normal_r1 = build_sample(pair['normal']['R1'])
    normal_r2 = build_sample(pair['normal']['R2'])
    tumor_r1 = build_sample(pair['tumor']['R1'])
    tumor_r2 = build_sample(pair['tumor']['R2'])

    # merge the dict's; the second dict will overwrite args from the first
    normal = {**normal_r1, **normal_r2}
    normal['R1'] = file_to_cwl(pair['normal']['R1'].file)
    normal['R2'] = file_to_cwl(pair['normal']['R2'].file)

    tumor = {**tumor_r1, **tumor_r2}
    tumor['R1'] = file_to_cwl(pair['tumor']['R1'].file)
    tumor['R2'] = file_to_cwl(pair['tumor']['R2'].file)

    output = (tumor, normal)
    return(output)

def bams_to_cwl(bams):
    """
    Convert the items in the bams list to CWL format

    bams = [ [File.objects.get(file_name = 's_C_K2902H_P001_d.rg.md.abra.printreads.bam'), File.objects.get(file_name = 's_C_K2902H_N001_d.rg.md.abra.printreads.bam')], ... ]
    """
    bam_cwls = []
    for item in bams:
        tumor_bam = item[0]
        normal_bam = item[1]
        tumor_bam_cwl = file_to_cwl(tumor_bam)
        normal_bam_cwl = file_to_cwl(normal_bam)
        bam_cwls.append([tumor_bam_cwl, normal_bam_cwl])
    return(bam_cwls)

def parse_runparams_from_ports(ports_queryset):
    """
    Get the runparams from a Port queryset
    """
    # TODO: how to ensure the correct number of Port items? Should be 1
    param_port = ports_queryset.filter(name = "runparams").first()
    runparams = {}
    runparams['project_prefix'] = param_port.value['project_prefix'][0] # NOTE: comes in as array but need single string
    runparams['genome'] = param_port.value['genome']
    runparams['scripts_bin'] = param_port.value['scripts_bin']

    # TODO: find a way to handle
    runparams['pi'] = "NA"
    runparams['pi_email'] = "NA"
    return(runparams)

def get_db_files(assay, references_json = "runner/operator/roslin_operator/reference_jsons/roslin_resources.json"):
    """
    Return a dict with the required reference file paths
    """
    references = json.load(open(references_json))
    db_files = {}
    db_files['fp_genotypes'] = references["targets"][assay]['FP_genotypes']
    db_files['hotspot_list_maf'] = references["request_files"]['hotspot_list_maf']
    db_files['conpair_markers'] = references["request_files"]['conpair_markers']
    db_files['ref_fasta'] = references["request_files"]['ref_fasta']

    # check for URI ref_fasta; 'juno:///juno/work/ci/resources/genomes/GRCh37/fasta/b37.fasta'
    for key, value in db_files.items():
        if value.startswith('juno:///'):
            parts = urllib.parse.urlsplit(value)
            db_files[key] = path_to_cwl(parts.path)
        elif value.startswith('/'):
            db_files[key] = path_to_cwl(value)
        # TODO: what to do if its not either of these cases?

    return(db_files)

def parse_outputs_files_data(files_data):
    """
    Generate an input dataset from a list of dicts of File objects and their associated Port.name value
    Uses items that came from a pipeline output

    files_data = [{ 'name': Port.name, 'file': {'class': 'File', 'path': '/path/to/foo.txt'} }, ... ]
    """
    # initialize the output data to use for starting QC pipeline
    qc_input = {}
    qc_input['clstats1'] = []
    qc_input['clstats2'] = []
    qc_input['md_metrics'] = []
    qc_input['hs_metrics'] = []
    qc_input['insert_metrics'] = []
    qc_input['per_target_coverage'] = []
    qc_input['qual_metrics'] = []
    qc_input['doc_basecounts'] = []
    qc_input['conpair_pileups'] = []

    for item in files_data:
        item_type = item['name']
        file_cwl = item['file']

        # append values for known keys
        # TODO: do we need to enforce unique-ness here? Do we need to enfore unique on file basename as well?
        if item_type in qc_input:
            if file_cwl not in qc_input[item_type]:
                qc_input[item_type].append(file_cwl)
    return(qc_input)

def build_inputs_from_runs(run_queryset, _assay = None):
    """
    Build the Roslin QC pipeline inputs data structure from a set of Roslin Voyager pipeline Run instances
    """
    # get the input and output Ports of the run
    ports = Port.objects.filter(run__in = run_queryset).order_by('created_date') # arbitrary ordering to force a test-able output

    # get the list of tumor normal pairs out of the Ports
    pairs = parse_pairs_from_ports(ports)

    # convert the pairs to CWL format datastructure
    pairs_cwl = []
    for pair_set in pairs:
        pair_cwl = pair_to_cwl(pair_set)
        pairs_cwl.append(pair_cwl)

    # get the File entries while keeping Port.name; needed for later parsing
    files_data = create_files_data_from_ports_with_names(ports)
    input_files = parse_outputs_files_data(files_data)

    # need to get the assay type so that we can get the correct reference files later
    # TODO: how to handle multiple runs? just use the first one for now...
    if _assay == None:
        assay = get_assay_from_run(run_queryset.first())
    else:
        assay = str(_assay)

    # find the Port with 'runparams' needed for QC input
    runparams = parse_runparams_from_ports(ports)
    runparams['assay'] = assay

    # get the correct reference files based on assay type
    db_files = get_db_files(assay)
    ref_fasta = db_files.pop('ref_fasta')

    # get the .bam files needed for QC input
    bams = parse_bams_from_ports(ports)

    # convert to CWL output format
    bams_cwl = bams_to_cwl(bams)

    # build the final data dict for QC input
    qc_input = {}
    qc_input['db_files'] = db_files
    qc_input['runparams'] = runparams
    qc_input['pairs'] = pairs_cwl
    qc_input['ref_fasta'] = ref_fasta
    qc_input['bams'] = bams_cwl
    qc_input['directories'] = []
    qc_input['files'] = []
    qc_input = {**qc_input, **input_files}

    return(qc_input)
