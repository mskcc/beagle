"""
Test for constructing ultron inputs
"""
import os
import json
from pprint import pprint
from uuid import UUID
from django.test import TestCase
from beagle_etl.models import Operator
from notifier.models import JobGroup
from file_system.models import File, FileMetadata, FileGroup, FileType
from file_system.repository.file_repository import FileRepository
from django.conf import settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient


class TestUltron(TestCase):
    # load fixtures for the test case temp db
    fixtures = [
        "file_system.filegroup.json",
        "file_system.filetype.json",
        "file_system.storage.json",
        "DMP_data.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.samples.json",
        "28ca34e8-9d4c-4543-9fc7-981bf5f6a97f.files.json",
        "4d9c8213-df56-4a0f-8d86-ce2bd8349c59.samples.json",
        "4d9c8213-df56-4a0f-8d86-ce2bd8349c59.files.json",
        "request_files.json",
        'request_metadata.json'
    ]

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        settings.DMP_BAM_FILE_GROUP = "6b3bf1ec-4cc0-441c-8fd7-0c104091cd58"
        self.response_csv = 'igoRequestId,primaryId,cmoPatientId,cmoSampleIdFields,dmpPatientId,dmpImpactSamples,dmpAccessSamples,baitSet,libraryVolume,investigatorSampleId,preservation,species,libraryConcentrationNgul,tissueLocation,sampleClass,sex,cfDNA2dBarcode,sampleOrigin,tubeId,tumorOrNormal,captureConcentrationNm,oncotreeCode,dnaInputNg,collectionYear,captureInputNg\r\n12345_A,12345_A_1,C-ALLANT2,,P-0000002,P-0000005-T01-IM6;P-0000004-T01-IM6,,MSK-ACCESS-v1_0-probesAllwFP,25.0,P-REDACT,,,69.0,,,M,,Whole Blood,,Normal,14.49275362,,200.0,,999.99999978\r\n12345_A,12345_A_3,C-ALLANT,"{\'recipe\': \'MSK-ACCESS_v1\', \'sampleType\': \'DNA\', \'naToExtract\': \'\', \'normalizedPatientId\': \'P-REDACT\'}",P-0000001,P-0000002-T01-IM6;P-0000001-T01-IM6,,MSK-ACCESS-v1_0-probesAllwFP,25.0,P-REDACT,EDTA-Streck,,102.5,,Blood,M,8042889270,Whole Blood,,Normal,9.756097561,,200.0,,1000.0000000025001\r\n12345_A,12345_A_2,C-ALLANT,"{\'recipe\': \'MSK-ACCESS_v1\', \'sampleType\': \'DNA\', \'naToExtract\': \'\', \'normalizedPatientId\': \'P-REDACT\'}",P-0000001,P-0000002-T01-IM6;P-0000001-T01-IM6,,MSK-ACCESS-v1_0-probesAllwFP,25.0,P-REDACT,EDTA-Streck,,74.5,,Blood,M,8042889270,Whole Blood,,Normal,13.42281879,,200.0,,999.999999855\r\n'

    def test_manifest_endpoint(self):
        """
        """
        # make a GET request to the API endpoint
        response = self.client.get('/v0/fs/manifest/?request_id=12345_A')
        # check that the response status code is 200
        self.assertEqual(response.status_code, 200)
        # check that the response contains the correct data
        response_data = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_data, self.response_csv)
