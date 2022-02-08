"""
Test for constructing Argos samples
"""
from uuid import UUID
from django.conf import settings
from django.test import TestCase
from runner.operator.argos_operator.v1_0_0.bin.make_sample import build_sample
import json


class TestMakeSample(TestCase):

    def test_build_sample1(self):
        """
        Test for building a sample
        """
        data = [
            {'file_name': 'JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R1_001.fastq.gz',
             'id': UUID('a46c5e6b-0793-4cd2-b5dd-92b3d71cf1ac'),
             'metadata': {'R': 'R1',
                          'baitSet': 'IMPACT468_BAITS',
                          'barcodeId': None,
                          'barcodeIndex': None,
                          'captureConcentrationNm': '10.377358490566039',
                          'captureInputNg': '110.0',
                          'captureName': 'Pool-05257_CD-06287_AY-10075_D_2-Tube2_1',
                          settings.CMO_SAMPLE_CLASS_METADATA_KEY: 'Normal',
                          'collectionYear': '',
                          'dataAnalystEmail': '',
                          'dataAnalystName': '',
                          'externalSampleId': 'JW_MEL_007_NORM',
                          'flowCellId': 'HCYYWBBXY',
                          'flowCellLanes': [1, 2, 3],
                          'igocomplete': True,
                          'investigatorEmail': 'email2@internet.com',
                          'investigatorName': 'Jane Doe',
                          'investigatorSampleId': 'JW_MEL_007_NORM',
                          'labHeadEmail': 'email@internet.com',
                          'labHeadName': 'John Smith',
                          'libraryConcentrationNgul': 10.6,
                          settings.LIBRARY_ID_METADATA_KEY: '10075_D_2_3',
                          'libraryVolume': None,
                          settings.ONCOTREE_METADATA_KEY: None,
                          settings.PATIENT_ID_METADATA_KEY: 'C-8VK0V7',
                          'piEmail': '',
                          'preservation': 'EDTA-Streck',
                          'projectManagerName': '',
                          'readLength': '101/8/8/101',
                          settings.RECIPE_METADATA_KEY: 'IMPACT468',
                          settings.REQUEST_ID_METADATA_KEY: '10075_D_2',
                          'sequencingCenter': 'MSKCC',
                          'platform': 'Illumina',
                          'runDate': '2019-12-12',
                          'runId': 'JAX_0397',
                          'runMode': 'HiSeq High Output',
                          settings.SAMPLE_ID_METADATA_KEY: '10075_D_2_3',
                          settings.CMO_SAMPLE_NAME_METADATA_KEY: 'C-8VK0V7-N001-d',
                          'sampleOrigin': 'Plasma',
                          'sex': 'F',
                          'species': 'Human',
                          settings.SAMPLE_CLASS_METADATA_KEY: 'Blood',
                          'tissueLocation': '',
                          'tumorOrNormal': 'Normal'},
             'path': '/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_2/Sample_JW_MEL_007_NORM_IGO_10075_D_2_3/JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R1_001.fastq.gz'},
            {'file_name': 'JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R2_001.fastq.gz',
             'id': UUID('c71c259a-ebc0-4490-9af1-bc99387a70d7'),
             'metadata': {'R': 'R2',
                          'baitSet': 'IMPACT468_BAITS',
                          'barcodeId': None,
                          'barcodeIndex': None,
                          'captureConcentrationNm': '10.377358490566039',
                          'captureInputNg': '110.0',
                          'captureName': 'Pool-05257_CD-06287_AY-10075_D_2-Tube2_1',
                          settings.CMO_SAMPLE_CLASS_METADATA_KEY: 'Normal',
                          'collectionYear': '',
                          'dataAnalystEmail': '',
                          'dataAnalystName': '',
                          'externalSampleId': 'JW_MEL_007_NORM',
                          'flowCellId': 'HCYYWBBXY',
                          'flowCellLanes': [1, 2, 3],
                          'igocomplete': True,
                          'investigatorEmail': 'email2@internet.com',
                          'investigatorName': 'Jane Doe',
                          'investigatorSampleId': 'JW_MEL_007_NORM',
                          'labHeadEmail': 'email@internet.com',
                          'labHeadName': 'John Smith',
                          'libraryConcentrationNgul': 10.6,
                          'libraryIgoId': None,
                          'libraryVolume': None,
                          settings.ONCOTREE_METADATA_KEY: None,
                          settings.PATIENT_ID_METADATA_KEY: 'C-8VK0V7',
                          'piEmail': '',
                          'preservation': 'EDTA-Streck',
                          'projectManagerName': '',
                          'readLength': '101/8/8/101',
                          settings.RECIPE_METADATA_KEY: 'IMPACT468',
                          settings.REQUEST_ID_METADATA_KEY: '10075_D_2',
                          'sequencingCenter': 'MSKCC',
                          'platform': 'Illumina',
                          'runDate': '2019-12-12',
                          'runId': 'JAX_0397',
                          'runMode': 'HiSeq High Output',
                          settings.SAMPLE_ID_METADATA_KEY: '10075_D_2_3',
                          settings.CMO_SAMPLE_NAME_METADATA_KEY: 'C-8VK0V7-N001-d',
                          'sampleOrigin': 'Plasma',
                          'sex': 'F',
                          'species': 'Human',
                          settings.SAMPLE_CLASS_METADATA_KEY: 'Blood',
                          'tissueLocation': '',
                          'tumorOrNormal': 'Normal'},
             'path': '/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_2/Sample_JW_MEL_007_NORM_IGO_10075_D_2_3/JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R2_001.fastq.gz'}]

        sample = build_sample(data)

        expected_sample = {'CN': 'MSKCC',
                           'ID': ['s_C_8VK0V7_N001_d_HCYYWBBXY'],
                           'LB': '10075_D_2_3',
                           'PL': 'Illumina',
                           'PU': ['HCYYWBBXY'],
                           'R1': [
                               '/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_2/Sample_JW_MEL_007_NORM_IGO_10075_D_2_3/JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R1_001.fastq.gz'],
                           'R1_bid': [UUID('a46c5e6b-0793-4cd2-b5dd-92b3d71cf1ac')],
                           'R2': [
                               '/ifs/archive/GCL/hiseq/FASTQ/JAX_0397_BHCYYWBBXY/Project_10075_D_2/Sample_JW_MEL_007_NORM_IGO_10075_D_2_3/JW_MEL_007_NORM_IGO_10075_D_2_3_S15_R2_001.fastq.gz'],
                           'R2_bid': [UUID('c71c259a-ebc0-4490-9af1-bc99387a70d7')],
                           'bam': [],
                           'bam_bid': [],
                           'SM': 's_C_8VK0V7_N001_d',
                           'bait_set': 'IMPACT468_BAITS',
                           'sample_id': '10075_D_2_3',
                           'patient_id': 'C-8VK0V7',
                           'request_id': '10075_D_2',
                           'run_date': ['2019-12-12'],
                           'run_id': ['JAX_0397'],
                           'preservation_type': ['EDTA-Streck'],
                           'species': 'Human',
                           'specimen_type': 'Blood',
                           'tumor_type': 'Normal',
                           'pi': 'John Smith',
                           'pi_email': 'email@internet.com'}

        print("Testing build_sample ---")
        print(json.dumps(sample, cls=UUIDEncoder))
        print(json.dumps(expected_sample, cls=UUIDEncoder))

        self.assertTrue(sample == expected_sample)

class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return obj.hex
        return json.JSONEncoder.default(self, obj)
