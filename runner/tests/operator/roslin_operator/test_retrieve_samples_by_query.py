from django.test import TestCase
from django.db.models import Prefetch, Q
from runner.operator.roslin_operator.bin.retrieve_samples_by_query import build_dmp_query

class TestRetrieveSamplesByQuery(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
    "file_system.filegroup.json",
    "file_system.filetype.json",
    "file_system.storage.json"
    ]

    def test_build_dmp_query1(self):
        """
        Test that DMP query is built correctly given different input parameters
        """
        # with dummy values
        patient_id = "foo"
        bait_set = "bar"
        dmp_query = build_dmp_query(patient_id, bait_set)
        expected_query =  Q(filemetadata__metadata__cmo_assay='') & Q(filemetadata__metadata__patient__cmo='foo') & Q(filemetadata__metadata__type='N')
        # (AND: ('filemetadata__metadata__cmo_assay', ''), ('filemetadata__metadata__patient__cmo', 'foo'), ('filemetadata__metadata__type', 'N'))
        self.assertEqual(dmp_query, expected_query)

        # with dummy CMO-ID style patient ID
        patient_id = "C-foo"
        bait_set = "bar"
        dmp_query = build_dmp_query(patient_id, bait_set)
        expected_query =  Q(filemetadata__metadata__cmo_assay='') & Q(filemetadata__metadata__patient__cmo='foo') & Q(filemetadata__metadata__type='N')
        self.assertEqual(dmp_query, expected_query)

        # dummy CMO-ID style patient ID and partially matching bait_set impact341
        patient_id = "C-foo1"
        bait_set = "IMPACT341_foo"
        dmp_query = build_dmp_query(patient_id, bait_set)
        expected_query =  Q(filemetadata__metadata__cmo_assay='IMPACT341') & Q(filemetadata__metadata__patient__cmo='foo1') & Q(filemetadata__metadata__type='N')
        self.assertEqual(dmp_query, expected_query)
