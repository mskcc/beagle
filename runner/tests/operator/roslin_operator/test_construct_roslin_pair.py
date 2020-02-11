"""
Test for constructing Roslin pair and jobs
"""
import os
import json
from pprint import pprint
from uuid import UUID
from django.test import TestCase
from runner.operator.roslin_operator.construct_roslin_pair import construct_roslin_jobs
from runner.operator.roslin_operator.construct_roslin_pair import get_baits_and_targets
from runner.operator.roslin_operator.construct_roslin_pair import get_target_assay
from runner.operator.roslin_operator.construct_roslin_pair import InvalidAssay
from runner.operator.roslin_operator.bin.make_sample import build_sample
from file_system.models import File, FileMetadata, FileGroup, FileType
from django.conf import settings
from django.core.management import call_command

class TestConstructPair(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json"
    ]

    def setUp(self):
        os.environ['TMPDIR'] = ''

    def test_construct_roslin_jobs1(self):
        """
        Test that Roslin jobs are correctly created
        """
        # Load fixtures
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.file.json")
        call_command('loaddata', test_files_fixture, verbosity=0)
        test_files_fixture = os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.filemetadata.json")
        call_command('loaddata', test_files_fixture, verbosity=0)

        files = File.objects.filter(filemetadata__metadata__requestId = "10075_D", filemetadata__metadata__igocomplete = True).all()
        data = list()
        for file in files:
            sample = dict()
            sample['id'] = file.id
            sample['path'] = file.path
            sample['file_name'] = file.file_name
            sample['metadata'] = file.filemetadata_set.first().metadata
            data.append(sample)
        samples = list()
        # group by igoId
        igo_id_group = dict()
        for sample in data:
            igo_id = sample['metadata']['sampleId']
            if igo_id not in igo_id_group:
                igo_id_group[igo_id] = list()
            igo_id_group[igo_id].append(sample)

        for igo_id in igo_id_group:
            samples.append(build_sample(igo_id_group[igo_id]))

        roslin_inputs, error_samples = construct_roslin_jobs(samples)
        # pprint(">>> roslin_inputs: ")
        # print(json.dumps(roslin_inputs, indent = 4))
        expected_inputs = json.load(open(os.path.join(settings.TEST_FIXTURE_DIR, "10075_D_single_TN_pair.roslin.input.json")))
        self.assertTrue(roslin_inputs == expected_inputs)

    def test_get_baits_and_targets1(self):
        """
        Test that the correct baits and targets are returned for a given assay
        """
        roslin_resources = json.load(open("runner/operator/roslin_operator/reference_jsons/roslin_resources.json", 'rb'))
        targets = roslin_resources['targets']

        # invalid assay throws a TypeError
        with self.assertRaises(InvalidAssay):
            get_baits_and_targets(assay = "foo", roslin_resources = roslin_resources)

        # known combinations of assay label pattern vs. true assay type to use for targets lookup
        combinations = [
        ("IMPACT410", "IMPACT410_b37"),
        ("IMPACT468", "IMPACT468_b37"),
        ("IMPACT341", "IMPACT341_b37"),
        ("IDT_Exome_v1_FP", "IDT_Exome_v1_FP_b37"),
        ("IMPACT468+08390", "IMPACT468_08390"),
        ("IMPACT468+Poirier_RB1_intron_V2", "IMPACT468_08050")
        ]

        for find_assay, target_assay in combinations:
            expected_targets = {"bait_intervals": {"class": "File", 'location': str(targets[target_assay]['baits_list'])},
                    "target_intervals": {"class": "File", 'location': str(targets[target_assay]['targets_list'])},
                    "fp_intervals": {"class": "File", 'location': str(targets[target_assay]['FP_intervals'])},
                    "fp_genotypes": {"class": "File", 'location': str(targets[target_assay]['FP_genotypes'])}}
            self.assertEqual( get_baits_and_targets(assay = find_assay, roslin_resources = roslin_resources), expected_targets)

    def test_get_target_assay1(self):
        """
        Test that the correct target assay label is returned for a given assay label which might be different from the actual target assay to use
        """
        with self.assertRaises(InvalidAssay):
            get_target_assay(assay = "foo")

        # known combinations of assay label pattern vs. true assay type to use for targets lookup
        combinations = [
        ("IMPACT410", "IMPACT410_b37"),
        ("IMPACT468", "IMPACT468_b37"),
        ("IMPACT341", "IMPACT341_b37"),
        ("IDT_Exome_v1_FP", "IDT_Exome_v1_FP_b37"),
        ("IMPACT468+08390", "IMPACT468_08390"),
        ("IMPACT468+Poirier_RB1_intron_V2", "IMPACT468_08050")
        ]
        for find_assay, target_assay in combinations:
            self.assertEqual( get_target_assay(assay = find_assay), target_assay)
