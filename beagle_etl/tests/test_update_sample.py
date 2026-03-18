import json
from django.test import TestCase
from beagle_etl.smile_message.objects.update_sample import UpdateSample


class TestUpdateSampleDeserialization(TestCase):
    def setUp(self):
        """Set up test data with anonymized JSON."""
        self.json_data = {
            "smileSampleId": "3614e17a-012b-4d45-8054-44805b99a0da",
            "sampleAliases": [
                {"value": "TestSample_N18", "namespace": "investigatorId"},
                {"value": "12345_B_7", "namespace": "igoId"},
            ],
            "patient": {
                "smilePatientId": "9c887ad1-7a07-4b94-8a1d-911bc2ba40a7",
                "patientAliases": [{"value": "C-TEST123", "namespace": "cmoId"}],
                "cmoPatientId": {"value": "C-TEST123", "namespace": "cmoId"},
            },
            "sampleMetadataList": [
                {
                    "primaryId": "12345_B_7",
                    "cmoPatientId": "C-TEST456",
                    "investigatorSampleId": "TestSample_N18",
                    "cmoSampleName": "C-TEST456-F001-d01",
                    "sampleName": "TestSample_N18",
                    "igoRequestId": "12345_B",
                    "importDate": "2026-02-03",
                    "cmoInfoIgoId": "12345_B_7",
                    "oncotreeCode": None,
                    "collectionYear": "",
                    "tubeId": "037038_7",
                    "cfDNA2dBarcode": None,
                    "species": "Human",
                    "sex": "Female",
                    "tumorOrNormal": "Normal",
                    "sampleType": "Normal",
                    "preservation": "Fresh",
                    "sampleClass": "Non-PDX",
                    "sampleOrigin": "",
                    "tissueLocation": "",
                    "genePanel": "HC_IMPACT",
                    "baitSet": "IMPACT505_BAITS",
                    "igoComplete": True,
                    "qcReports": [
                        {
                            "qcReportType": "DNA",
                            "comments": "",
                            "investigatorDecision": "Already moved forward by IGO",
                            "din": None,
                            "IGORecommendation": "Passed",
                        }
                    ],
                    "libraries": [
                        {
                            "barcodeId": None,
                            "barcodeIndex": None,
                            "libraryIgoId": "12345_B_7",
                            "libraryVolume": None,
                            "libraryConcentrationNgul": None,
                            "dnaInputNg": None,
                            "captureConcentrationNm": "3.125",
                            "captureInputNg": "110.00000000000001",
                            "captureName": "Pool-12345_B-B2_1",
                            "runs": [
                                {
                                    "runMode": "NovaSeq X 10B",
                                    "runId": "TEST_RUN_0126",
                                    "flowCellId": "TEST123LT3",
                                    "readLength": "101/8/8/101",
                                    "runDate": "2026-01-29",
                                    "flowCellLanes": [5, 6, 7, 8],
                                    "fastqs": [
                                        "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L008_R1_001.fastq.gz",
                                        "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L008_R2_001.fastq.gz",
                                    ],
                                }
                            ],
                        }
                    ],
                    "cmoSampleIdFields": {
                        "naToExtract": "DNA",
                        "normalizedPatientId": "TEST_PATIENT_N18",
                        "sampleType": "Fingernails",
                        "recipe": "HC_IMPACT",
                    },
                    "additionalProperties": {
                        "isCmoSample": "true",
                        "igoSampleStatus": "Completed DNA Extraction",
                        "altId": "ACB-TEST",
                        "igoRequestId": "12345_B",
                    },
                    "status": {
                        "validationStatus": False,
                        "validationReport": '{"sample type abbreviation":"could not resolve based on sampleClass"}',
                    },
                    "sampleAliases": [],
                    "patientAliases": [],
                    "smileSampleId": "3614e17a-012b-4d45-8054-44805b99a0da",
                    "smilePatientId": "9c887ad1-7a07-4b94-8a1d-911bc2ba40a7",
                    "datasource": "igo",
                },
                {
                    "primaryId": "12345_B_7",
                    "cmoPatientId": "C-TEST123",
                    "investigatorSampleId": "TestSample_N18",
                    "cmoSampleName": "C-TEST123-F003-d01",
                    "sampleName": "TestSample_N18",
                    "igoRequestId": "12345_B",
                    "importDate": "2026-02-19",
                    "cmoInfoIgoId": "12345_B_7",
                    "oncotreeCode": None,
                    "collectionYear": "",
                    "tubeId": "037038_7",
                    "cfDNA2dBarcode": None,
                    "species": "Human",
                    "sex": "Female",
                    "tumorOrNormal": "Normal",
                    "sampleType": "Normal",
                    "preservation": "Fresh",
                    "sampleClass": "Non-PDX",
                    "sampleOrigin": "",
                    "tissueLocation": "",
                    "genePanel": "HC_IMPACT",
                    "baitSet": "IMPACT505_BAITS",
                    "igoComplete": True,
                    "qcReports": [
                        {
                            "qcReportType": "LIBRARY",
                            "comments": "",
                            "investigatorDecision": "",
                            "din": None,
                            "IGORecommendation": "Passed",
                        }
                    ],
                    "libraries": [
                        {
                            "barcodeId": None,
                            "barcodeIndex": None,
                            "libraryIgoId": "12345_B_7",
                            "libraryVolume": None,
                            "libraryConcentrationNgul": None,
                            "dnaInputNg": None,
                            "captureConcentrationNm": "3.125",
                            "captureInputNg": "110.00000000000001",
                            "captureName": "Pool-12345_B-B2_1",
                            "runs": [
                                {
                                    "runMode": "NovaSeq X 10B",
                                    "runId": "TEST_RUN_0126",
                                    "flowCellId": "TEST123LT3",
                                    "readLength": "101/8/8/101",
                                    "runDate": "2026-01-29",
                                    "flowCellLanes": [5, 6, 7, 8],
                                    "fastqs": [
                                        "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L005_R1_001.fastq.gz",
                                        "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L005_R2_001.fastq.gz",
                                    ],
                                }
                            ],
                        }
                    ],
                    "cmoSampleIdFields": {
                        "naToExtract": "DNA",
                        "normalizedPatientId": "TEST_PATIENT_N18",
                        "sampleType": "Fingernails",
                        "recipe": "HC_IMPACT",
                    },
                    "additionalProperties": {
                        "isCmoSample": "true",
                        "igoSampleStatus": "Completed DNA Extraction",
                        "altId": "ACB-TEST",
                        "igoRequestId": "12345_B",
                    },
                    "status": {
                        "validationStatus": False,
                        "validationReport": '{"sample type abbreviation":"could not resolve based on sampleClass"}',
                    },
                    "sampleAliases": [],
                    "patientAliases": [],
                    "smileSampleId": "3614e17a-012b-4d45-8054-44805b99a0da",
                    "smilePatientId": "9c887ad1-7a07-4b94-8a1d-911bc2ba40a7",
                    "datasource": "igo",
                },
            ],
            "tempo": None,
            "dbGap": None,
            "sampleClass": "Normal",
            "sampleCategory": "research",
            "datasource": "igo",
            "revisable": True,
            "primarySampleAlias": "12345_B_7",
            "latestSampleMetadata": {
                "primaryId": "12345_B_7",
                "cmoPatientId": "C-TEST123",
                "investigatorSampleId": "TestSample_N18",
                "cmoSampleName": "C-TEST123-F003-d01",
                "sampleName": "TestSample_N18",
                "igoRequestId": "12345_B",
                "importDate": "2026-02-19",
                "cmoInfoIgoId": "12345_B_7",
                "oncotreeCode": None,
                "collectionYear": "",
                "tubeId": "037038_7",
                "cfDNA2dBarcode": None,
                "species": "Human",
                "sex": "Female",
                "tumorOrNormal": "Normal",
                "sampleType": "Normal",
                "preservation": "Fresh",
                "sampleClass": "Non-PDX",
                "sampleOrigin": "",
                "tissueLocation": "",
                "genePanel": "HC_IMPACT",
                "baitSet": "IMPACT505_BAITS",
                "igoComplete": True,
                "qcReports": [
                    {
                        "qcReportType": "DNA",
                        "comments": "",
                        "investigatorDecision": "Already moved forward by IGO",
                        "din": None,
                        "IGORecommendation": "Passed",
                    },
                    {
                        "qcReportType": "LIBRARY",
                        "comments": "",
                        "investigatorDecision": "",
                        "din": None,
                        "IGORecommendation": "Passed",
                    },
                ],
                "libraries": [
                    {
                        "barcodeId": None,
                        "barcodeIndex": None,
                        "libraryIgoId": "12345_B_7",
                        "libraryVolume": None,
                        "libraryConcentrationNgul": None,
                        "dnaInputNg": None,
                        "captureConcentrationNm": "3.125",
                        "captureInputNg": "110.00000000000001",
                        "captureName": "Pool-12345_B-B2_1",
                        "runs": [
                            {
                                "runMode": "NovaSeq X 10B",
                                "runId": "TEST_RUN_0126",
                                "flowCellId": "TEST123LT3",
                                "readLength": "101/8/8/101",
                                "runDate": "2026-01-29",
                                "flowCellLanes": [5, 6, 7, 8],
                                "fastqs": [
                                    "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L008_R1_001.fastq.gz",
                                    "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L008_R2_001.fastq.gz",
                                    "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L007_R2_001.fastq.gz",
                                    "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L007_R1_001.fastq.gz",
                                    "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L006_R1_001.fastq.gz",
                                    "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L006_R2_001.fastq.gz",
                                    "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L005_R1_001.fastq.gz",
                                    "/igo/delivery/FASTQ/TEST_RUN_0126/Project_12345_B/Sample_N18_IGO_12345_B_7/N18_IGO_12345_B_7_S63_L005_R2_001.fastq.gz",
                                ],
                            }
                        ],
                    }
                ],
                "cmoSampleIdFields": {
                    "naToExtract": "DNA",
                    "normalizedPatientId": "TEST_PATIENT_N18",
                    "sampleType": "Fingernails",
                    "recipe": "HC_IMPACT",
                },
                "additionalProperties": {
                    "isCmoSample": "true",
                    "igoSampleStatus": "Completed DNA Extraction",
                    "altId": "ACB-TEST",
                    "igoRequestId": "12345_B",
                },
                "status": {
                    "validationStatus": False,
                    "validationReport": '{"sample type abbreviation":"could not resolve based on sampleClass"}',
                },
                "sampleAliases": [],
                "patientAliases": [],
                "smileSampleId": "3614e17a-012b-4d45-8054-44805b99a0da",
                "smilePatientId": "9c887ad1-7a07-4b94-8a1d-911bc2ba40a7",
                "datasource": "igo",
            },
        }

    def test_deserialize_update_sample(self):
        """Test deserialization of JSON to UpdateSample object."""
        update_sample = UpdateSample.from_dict(self.json_data)

        # Assert top-level fields
        self.assertEqual(update_sample.smileSampleId, "3614e17a-012b-4d45-8054-44805b99a0da")
        self.assertEqual(update_sample.sampleClass, "Normal")
        self.assertEqual(update_sample.sampleCategory, "research")
        self.assertEqual(update_sample.datasource, "igo")
        self.assertTrue(update_sample.revisable)
        self.assertEqual(update_sample.primarySampleAlias, "12345_B_7")
        self.assertIsNone(update_sample.tempo)
        self.assertIsNone(update_sample.dbGap)

    def test_deserialize_sample_aliases(self):
        """Test deserialization of sample aliases."""
        update_sample = UpdateSample.from_dict(self.json_data)

        self.assertEqual(len(update_sample.sampleAliases), 2)
        self.assertEqual(update_sample.sampleAliases[0].value, "TestSample_N18")
        self.assertEqual(update_sample.sampleAliases[0].namespace, "investigatorId")
        self.assertEqual(update_sample.sampleAliases[1].value, "12345_B_7")
        self.assertEqual(update_sample.sampleAliases[1].namespace, "igoId")

    def test_deserialize_patient_info(self):
        """Test deserialization of patient information."""
        update_sample = UpdateSample.from_dict(self.json_data)

        self.assertEqual(update_sample.patient.smilePatientId, "9c887ad1-7a07-4b94-8a1d-911bc2ba40a7")
        self.assertEqual(len(update_sample.patient.patientAliases), 1)
        self.assertEqual(update_sample.patient.patientAliases[0].value, "C-TEST123")
        self.assertEqual(update_sample.patient.patientAliases[0].namespace, "cmoId")
        self.assertEqual(update_sample.patient.cmoPatientId.value, "C-TEST123")
        self.assertEqual(update_sample.patient.cmoPatientId.namespace, "cmoId")

    def test_deserialize_sample_metadata_list(self):
        """Test deserialization of sample metadata list."""
        update_sample = UpdateSample.from_dict(self.json_data)

        self.assertEqual(len(update_sample.sampleMetadataList), 2)

        # Test first sample metadata
        sample1 = update_sample.sampleMetadataList[0]
        self.assertEqual(sample1.primaryId, "12345_B_7")
        self.assertEqual(sample1.cmoPatientId, "C-TEST456")
        self.assertEqual(sample1.igoRequestId, "12345_B")
        self.assertEqual(sample1.importDate, "2026-02-03")
        self.assertEqual(sample1.genePanel, "HC_IMPACT")
        self.assertTrue(sample1.igoComplete)

        # Test second sample metadata
        sample2 = update_sample.sampleMetadataList[1]
        self.assertEqual(sample2.primaryId, "12345_B_7")
        self.assertEqual(sample2.cmoPatientId, "C-TEST123")
        self.assertEqual(sample2.igoRequestId, "12345_B")
        self.assertEqual(sample2.importDate, "2026-02-19")

    def test_deserialize_latest_sample_metadata(self):
        """Test deserialization of latest sample metadata."""
        update_sample = UpdateSample.from_dict(self.json_data)

        latest = update_sample.latestSampleMetadata
        self.assertEqual(latest.primaryId, "12345_B_7")
        self.assertEqual(latest.cmoPatientId, "C-TEST123")
        self.assertEqual(latest.investigatorSampleId, "TestSample_N18")
        self.assertEqual(latest.cmoSampleName, "C-TEST123-F003-d01")
        self.assertEqual(latest.igoRequestId, "12345_B")
        self.assertEqual(latest.importDate, "2026-02-19")
        self.assertEqual(latest.genePanel, "HC_IMPACT")
        self.assertEqual(latest.baitSet, "IMPACT505_BAITS")
        self.assertTrue(latest.igoComplete)

    def test_deserialize_libraries_in_latest_metadata(self):
        """Test deserialization of libraries in latest sample metadata."""
        update_sample = UpdateSample.from_dict(self.json_data)

        latest = update_sample.latestSampleMetadata
        self.assertEqual(len(latest.libraries), 1)

        library = latest.libraries[0]
        self.assertEqual(library.libraryIgoId, "12345_B_7")
        self.assertEqual(library.captureConcentrationNm, "3.125")
        self.assertEqual(library.captureName, "Pool-12345_B-B2_1")

    def test_deserialize_runs_in_latest_metadata(self):
        """Test deserialization of runs in latest sample metadata."""
        update_sample = UpdateSample.from_dict(self.json_data)

        latest = update_sample.latestSampleMetadata
        library = latest.libraries[0]
        self.assertEqual(len(library.runs), 1)

        run = library.runs[0]
        self.assertEqual(run.runMode, "NovaSeq X 10B")
        self.assertEqual(run.runId, "TEST_RUN_0126")
        self.assertEqual(run.flowCellId, "TEST123LT3")
        self.assertEqual(run.readLength, "101/8/8/101")
        self.assertEqual(run.runDate, "2026-01-29")
        self.assertEqual(run.flowCellLanes, [5, 6, 7, 8])
        self.assertEqual(len(run.fastqs), 8)
        self.assertIn("R1_001.fastq.gz", run.fastqs[0])
        self.assertIn("R2_001.fastq.gz", run.fastqs[1])

    def test_deserialize_qc_reports(self):
        """Test deserialization of QC reports in latest metadata."""
        update_sample = UpdateSample.from_dict(self.json_data)

        latest = update_sample.latestSampleMetadata
        self.assertEqual(len(latest.qcReports), 2)
        self.assertEqual(latest.qcReports[0]["qcReportType"], "DNA")
        self.assertEqual(latest.qcReports[1]["qcReportType"], "LIBRARY")

    def test_deserialize_cmo_sample_id_fields(self):
        """Test deserialization of CMO sample ID fields."""
        update_sample = UpdateSample.from_dict(self.json_data)

        latest = update_sample.latestSampleMetadata
        self.assertEqual(latest.cmoSampleIdFields.naToExtract, "DNA")
        self.assertEqual(latest.cmoSampleIdFields.normalizedPatientId, "TEST_PATIENT_N18")
        self.assertEqual(latest.cmoSampleIdFields.sampleType, "Fingernails")
        self.assertEqual(latest.cmoSampleIdFields.recipe, "HC_IMPACT")

    def test_deserialize_status(self):
        """Test deserialization of validation status."""
        update_sample = UpdateSample.from_dict(self.json_data)

        latest = update_sample.latestSampleMetadata
        self.assertFalse(latest.status.validationStatus)
        self.assertIn("sample type abbreviation", latest.status.validationReport)

    def test_to_dict_round_trip(self):
        """Test that to_dict returns data that can be deserialized again."""
        update_sample = UpdateSample.from_dict(self.json_data)
        serialized = update_sample.to_dict()

        # Deserialize again
        update_sample2 = UpdateSample.from_dict(serialized)

        # Compare key fields
        self.assertEqual(update_sample.smileSampleId, update_sample2.smileSampleId)
        self.assertEqual(update_sample.primarySampleAlias, update_sample2.primarySampleAlias)
        self.assertEqual(update_sample.latestSampleMetadata.primaryId, update_sample2.latestSampleMetadata.primaryId)
        self.assertEqual(len(update_sample.sampleMetadataList), len(update_sample2.sampleMetadataList))
