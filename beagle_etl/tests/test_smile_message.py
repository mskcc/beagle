import json
from django.test import TestCase
from beagle_etl.smile_message.objects import RequestMetadata, SampleMetadata


class TestSmileMessageDeserialization(TestCase):
    def setUp(self):
        """Set up test data with anonymized JSON."""
        self.json_data = {
            "smileRequestId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "igoProjectId": "12345",
            "igoRequestId": "12345_B",
            "igoDeliveryDate": None,
            "ilabRequestId": None,
            "genePanel": "TestPanel500",
            "projectManagerName": "Smith, John",
            "piEmail": "pi@example.org",
            "labHeadName": "Jane Doe",
            "labHeadEmail": "labhead@example.org",
            "investigatorName": "Bob Researcher",
            "investigatorEmail": "researcher@example.org",
            "dataAnalystName": "Alice Analyst",
            "dataAnalystEmail": "analyst@example.org",
            "otherContactEmails": "contact@example.org",
            "dataAccessEmails": "",
            "qcAccessEmails": "qc@example.org",
            "strand": "null",
            "libraryType": "null",
            "isCmoRequest": True,
            "bicAnalysis": True,
            "status": {"validationStatus": True, "validationReport": "{}"},
            "requestJson": '{"requestId":"12345_B"}',
            "pooledNormals": None,
            "samples": [
                {
                    "smileSampleId": "11111111-2222-3333-4444-555555555555",
                    "smilePatientId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "primaryId": "12345_B_1",
                    "cmoPatientId": "C-ABC123",
                    "cmoSampleName": "C-ABC123-T001-d",
                    "sampleName": "TEST001_Sample1",
                    "cmoInfoIgoId": None,
                    "investigatorSampleId": "TEST001_Sample1",
                    "importDate": "2024-01-15",
                    "sampleType": "Primary",
                    "oncotreeCode": "LUAD",
                    "collectionYear": "",
                    "tubeId": "",
                    "cfDNA2dBarcode": None,
                    "species": "Human",
                    "sex": "Male",
                    "tumorOrNormal": "Tumor",
                    "preservation": "Frozen",
                    "sampleClass": "Tissue",
                    "sampleOrigin": "Tissue",
                    "tissueLocation": "",
                    "genePanel": "TestPanel500",
                    "baitSet": "TestPanel500_BAITS",
                    "datasource": "igo",
                    "igoComplete": True,
                    "status": {"validationStatus": True, "validationReport": "{}"},
                    "cmoSampleIdFields": {
                        "naToExtract": "",
                        "normalizedPatientId": "TEST_PATIENT001",
                        "sampleType": "DNA",
                        "recipe": "TestPanel500",
                    },
                    "qcReports": [],
                    "libraries": [
                        {
                            "barcodeId": None,
                            "barcodeIndex": None,
                            "libraryIgoId": "12345_B_1_1_1_1",
                            "libraryVolume": 40,
                            "libraryConcentrationNgul": 25.5,
                            "dnaInputNg": None,
                            "captureConcentrationNm": "10.12345678901234",
                            "captureInputNg": "350.0",
                            "captureName": "Pool-12345_B-Tube1_1",
                            "runs": [
                                {
                                    "runMode": "NovaSeq Standard",
                                    "runId": "RUN_0001",
                                    "flowCellId": "TESTFC01",
                                    "readLength": "",
                                    "runDate": "2024-01-20",
                                    "flowCellLanes": [1],
                                    "fastqs": [
                                        "/data/fastq/RUN_0001_TESTFC01/Project_12345_B/Sample_TEST001_Sample1_IGO_12345_B_1/TEST001_Sample1_IGO_12345_B_1_S1_R1_001.fastq.gz",
                                        "/data/fastq/RUN_0001_TESTFC01/Project_12345_B/Sample_TEST001_Sample1_IGO_12345_B_1/TEST001_Sample1_IGO_12345_B_1_S1_R2_001.fastq.gz",
                                    ],
                                }
                            ],
                        }
                    ],
                    "sampleAliases": [
                        {"value": "TEST001_Sample1", "namespace": "investigatorId"},
                        {"value": "12345_B_1", "namespace": "igoId"},
                    ],
                    "patientAliases": [{"value": "C-ABC123", "namespace": "cmoId"}],
                    "additionalProperties": {"igoRequestId": "12345_B", "isCmoSample": "true", "altId": "T1A-V01"},
                },
                {
                    "smileSampleId": "22222222-3333-4444-5555-666666666666",
                    "smilePatientId": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                    "primaryId": "12345_B_2",
                    "cmoPatientId": "C-ABC123",
                    "cmoSampleName": "C-ABC123-N001-d",
                    "sampleName": "Normal_Sample_001",
                    "cmoInfoIgoId": None,
                    "investigatorSampleId": "Normal_Sample_001",
                    "importDate": "2024-01-15",
                    "sampleType": "Normal",
                    "oncotreeCode": None,
                    "collectionYear": "",
                    "tubeId": "",
                    "cfDNA2dBarcode": None,
                    "species": "Human",
                    "sex": "Male",
                    "tumorOrNormal": "Normal",
                    "preservation": "Frozen",
                    "sampleClass": "Blood",
                    "sampleOrigin": "Whole Blood",
                    "tissueLocation": "",
                    "genePanel": "TestPanel500",
                    "baitSet": "TestPanel500_BAITS",
                    "datasource": "igo",
                    "igoComplete": True,
                    "status": {"validationStatus": True, "validationReport": "{}"},
                    "cmoSampleIdFields": {
                        "naToExtract": "",
                        "normalizedPatientId": "TEST_PATIENT001",
                        "sampleType": "DNA",
                        "recipe": "TestPanel500",
                    },
                    "qcReports": [],
                    "libraries": [
                        {
                            "barcodeId": None,
                            "barcodeIndex": None,
                            "libraryIgoId": "12345_B_2_1_1_1",
                            "libraryVolume": 40,
                            "libraryConcentrationNgul": 28.3,
                            "dnaInputNg": None,
                            "captureConcentrationNm": "5.123456789012345",
                            "captureInputNg": "180.0",
                            "captureName": "Pool-12345_B-Tube1_1",
                            "runs": [
                                {
                                    "runMode": "NovaSeq Standard",
                                    "runId": "RUN_0001",
                                    "flowCellId": "TESTFC01",
                                    "readLength": "",
                                    "runDate": "2024-01-20",
                                    "flowCellLanes": [1],
                                    "fastqs": [
                                        "/data/fastq/RUN_0001_TESTFC01/Project_12345_B/Sample_Normal_Sample_001_IGO_12345_B_2/Normal_Sample_001_IGO_12345_B_2_S2_R1_001.fastq.gz",
                                        "/data/fastq/RUN_0001_TESTFC01/Project_12345_B/Sample_Normal_Sample_001_IGO_12345_B_2/Normal_Sample_001_IGO_12345_B_2_S2_R2_001.fastq.gz",
                                    ],
                                }
                            ],
                        }
                    ],
                    "sampleAliases": [
                        {"value": "Normal_Sample_001", "namespace": "investigatorId"},
                        {"value": "12345_B_2", "namespace": "igoId"},
                    ],
                    "patientAliases": [{"value": "C-ABC123", "namespace": "cmoId"}],
                    "additionalProperties": {"igoRequestId": "12345_B", "isCmoSample": "true", "altId": "T1A-V02"},
                },
            ],
        }

    def test_deserialize_request_metadata(self):
        """Test deserialization of JSON to RequestMetadata object."""
        # Deserialize
        request = RequestMetadata.from_dict(self.json_data)

        # Assert request-level fields
        self.assertEqual(request.smileRequestId, "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
        self.assertEqual(request.igoProjectId, "12345")
        self.assertEqual(request.igoRequestId, "12345_B")
        self.assertEqual(request.genePanel, "TestPanel500")
        self.assertEqual(request.projectManagerName, "Smith, John")
        self.assertEqual(request.piEmail, "pi@example.org")
        self.assertEqual(request.labHeadName, "Jane Doe")
        self.assertEqual(request.labHeadEmail, "labhead@example.org")
        self.assertEqual(request.investigatorName, "Bob Researcher")
        self.assertEqual(request.investigatorEmail, "researcher@example.org")
        self.assertEqual(request.dataAnalystName, "Alice Analyst")
        self.assertEqual(request.dataAnalystEmail, "analyst@example.org")
        self.assertTrue(request.isCmoRequest)
        self.assertTrue(request.bicAnalysis)
        self.assertIsNone(request.igoDeliveryDate)
        self.assertIsNone(request.pooledNormals)

        # Assert status
        self.assertTrue(request.status.validationStatus)
        self.assertEqual(request.status.validationReport, "{}")

        # Assert samples
        self.assertEqual(len(request.samples), 2)

    def test_deserialize_sample_metadata(self):
        """Test deserialization of sample data within request."""
        request = RequestMetadata.from_dict(self.json_data)

        # Test first sample (tumor)
        sample1 = request.samples[0]
        self.assertEqual(sample1.smileSampleId, "11111111-2222-3333-4444-555555555555")
        self.assertEqual(sample1.primaryId, "12345_B_1")
        self.assertEqual(sample1.cmoPatientId, "C-ABC123")
        self.assertEqual(sample1.cmoSampleName, "C-ABC123-T001-d")
        self.assertEqual(sample1.sampleName, "TEST001_Sample1")
        self.assertEqual(sample1.sampleType, "Primary")
        self.assertEqual(sample1.oncotreeCode, "LUAD")
        self.assertEqual(sample1.species, "Human")
        self.assertEqual(sample1.sex, "Male")
        self.assertEqual(sample1.tumorOrNormal, "Tumor")
        self.assertEqual(sample1.preservation, "Frozen")
        self.assertEqual(sample1.sampleClass, "Tissue")
        self.assertEqual(sample1.sampleOrigin, "Tissue")
        self.assertEqual(sample1.genePanel, "TestPanel500")
        self.assertEqual(sample1.baitSet, "TestPanel500_BAITS")
        self.assertEqual(sample1.datasource, "igo")
        self.assertTrue(sample1.igoComplete)

        # Test second sample (normal)
        sample2 = request.samples[1]
        self.assertEqual(sample2.primaryId, "12345_B_2")
        self.assertEqual(sample2.sampleType, "Normal")
        self.assertEqual(sample2.tumorOrNormal, "Normal")
        self.assertEqual(sample2.sampleClass, "Blood")
        self.assertIsNone(sample2.oncotreeCode)

    def test_deserialize_sample_status(self):
        """Test deserialization of sample status."""
        request = RequestMetadata.from_dict(self.json_data)
        sample = request.samples[0]

        self.assertTrue(sample.status.validationStatus)
        self.assertEqual(sample.status.validationReport, "{}")

    def test_deserialize_cmo_sample_id_fields(self):
        """Test deserialization of CMO sample ID fields."""
        request = RequestMetadata.from_dict(self.json_data)
        sample = request.samples[0]

        self.assertEqual(sample.cmoSampleIdFields.naToExtract, "")
        self.assertEqual(sample.cmoSampleIdFields.normalizedPatientId, "TEST_PATIENT001")
        self.assertEqual(sample.cmoSampleIdFields.sampleType, "DNA")
        self.assertEqual(sample.cmoSampleIdFields.recipe, "TestPanel500")

    def test_deserialize_libraries(self):
        """Test deserialization of libraries."""
        request = RequestMetadata.from_dict(self.json_data)
        sample = request.samples[0]

        self.assertEqual(len(sample.libraries), 1)

        library = sample.libraries[0]
        self.assertEqual(library.libraryIgoId, "12345_B_1_1_1_1")
        self.assertEqual(library.libraryVolume, 40.0)
        self.assertEqual(library.libraryConcentrationNgul, 25.5)
        self.assertEqual(library.captureConcentrationNm, "10.12345678901234")
        self.assertEqual(library.captureInputNg, "350.0")
        self.assertEqual(library.captureName, "Pool-12345_B-Tube1_1")
        self.assertIsNone(library.barcodeId)
        self.assertIsNone(library.barcodeIndex)
        self.assertIsNone(library.dnaInputNg)

    def test_deserialize_runs(self):
        """Test deserialization of runs within libraries."""
        request = RequestMetadata.from_dict(self.json_data)
        sample = request.samples[0]
        library = sample.libraries[0]

        self.assertEqual(len(library.runs), 1)

        run = library.runs[0]
        self.assertEqual(run.runMode, "NovaSeq Standard")
        self.assertEqual(run.runId, "RUN_0001")
        self.assertEqual(run.flowCellId, "TESTFC01")
        self.assertEqual(run.readLength, "")
        self.assertEqual(run.runDate, "2024-01-20")
        self.assertEqual(run.flowCellLanes, [1])
        self.assertEqual(len(run.fastqs), 2)
        self.assertIn("R1_001.fastq.gz", run.fastqs[0])
        self.assertIn("R2_001.fastq.gz", run.fastqs[1])

    def test_deserialize_sample_aliases(self):
        """Test deserialization of sample aliases."""
        request = RequestMetadata.from_dict(self.json_data)
        sample = request.samples[0]

        self.assertEqual(len(sample.sampleAliases), 2)

        alias1 = sample.sampleAliases[0]
        self.assertEqual(alias1.value, "TEST001_Sample1")
        self.assertEqual(alias1.namespace, "investigatorId")

        alias2 = sample.sampleAliases[1]
        self.assertEqual(alias2.value, "12345_B_1")
        self.assertEqual(alias2.namespace, "igoId")

    def test_deserialize_patient_aliases(self):
        """Test deserialization of patient aliases."""
        request = RequestMetadata.from_dict(self.json_data)
        sample = request.samples[0]

        self.assertEqual(len(sample.patientAliases), 1)

        alias = sample.patientAliases[0]
        self.assertEqual(alias.value, "C-ABC123")
        self.assertEqual(alias.namespace, "cmoId")

    def test_deserialize_additional_properties(self):
        """Test deserialization of additional properties."""
        request = RequestMetadata.from_dict(self.json_data)
        sample = request.samples[0]

        self.assertEqual(sample.additionalProperties["igoRequestId"], "12345_B")
        self.assertEqual(sample.additionalProperties["isCmoSample"], "true")
        self.assertEqual(sample.additionalProperties["altId"], "T1A-V01")

    def test_deserialize_qc_reports(self):
        """Test deserialization of QC reports (empty list in this case)."""
        request = RequestMetadata.from_dict(self.json_data)
        sample = request.samples[0]

        self.assertEqual(len(sample.qcReports), 0)
        self.assertIsInstance(sample.qcReports, list)

    def test_multiple_samples_same_patient(self):
        """Test that both samples belong to the same patient."""
        request = RequestMetadata.from_dict(self.json_data)

        # Both samples should have the same patient ID
        self.assertEqual(request.samples[0].smilePatientId, request.samples[1].smilePatientId)
        self.assertEqual(request.samples[0].cmoPatientId, request.samples[1].cmoPatientId)

    def test_sample_types_tumor_and_normal(self):
        """Test that we have both tumor and normal samples."""
        request = RequestMetadata.from_dict(self.json_data)

        sample_types = [sample.tumorOrNormal for sample in request.samples]
        self.assertIn("Tumor", sample_types)
        self.assertIn("Normal", sample_types)
