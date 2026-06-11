"""
Tests for persist_message callback function
"""
import json
from unittest.mock import Mock
from django.test import TestCase, TransactionTestCase
from django.conf import settings
from beagle_etl.models import SMILEMessage, SmileMessageStatus
from beagle_etl.smile_service.smile_callback import persist_message


class TestPersistMessage(TestCase):
    """Test that persist_message correctly creates SMILEMessage records from NATS messages."""

    def test_persist_new_request_message(self):
        """Test persisting a NEW_REQUEST message extracts request_id and gene_panel from root level."""
        # Create mock NATS message
        message_data = {
            settings.REQUEST_ID_METADATA_KEY: "08944_B",
            settings.RECIPE_METADATA_KEY: "IMPACT468",
            "igoProjectId": "08944",
            "labHeadName": "Test Researcher",
            "samples": [],
        }

        message = Mock()
        message.subject = settings.METADB_NATS_NEW_REQUEST
        message.data = json.dumps(message_data)

        # Call persist_message
        persist_message(message)

        # Verify SMILEMessage was created correctly
        smile_msg = SMILEMessage.objects.get(topic=settings.METADB_NATS_NEW_REQUEST)
        self.assertEqual(smile_msg.request_id, "08944_B")
        self.assertEqual(smile_msg.gene_panel, "IMPACT468")
        self.assertEqual(smile_msg.status, SmileMessageStatus.PENDING)
        self.assertEqual(smile_msg.message, message.data)

        # Verify data can be parsed back
        parsed_data = json.loads(smile_msg.message)
        self.assertEqual(parsed_data[settings.REQUEST_ID_METADATA_KEY], "08944_B")

    def test_persist_request_update_message(self):
        """Test persisting a REQUEST_UPDATE message (array format) extracts request_id and gene_panel."""
        # REQUEST_UPDATE is an array of request metadata updates
        message_data = [
            {
                settings.REQUEST_ID_METADATA_KEY: "10075_D",
                "requestMetadataJson": json.dumps(
                    {
                        "requestId": "10075_D",
                        settings.RECIPE_METADATA_KEY: "IMPACT468",
                        "labHeadName": "Test Researcher",
                        "investigatorName": "Test Investigator",
                    }
                ),
                "importDate": "2023-03-08",
                "status": {"validationStatus": True, "validationReport": "{}"},
            }
        ]

        message = Mock()
        message.subject = settings.METADB_NATS_REQUEST_UPDATE
        message.data = json.dumps(message_data)

        # Call persist_message
        persist_message(message)

        # Verify SMILEMessage was created correctly
        smile_msg = SMILEMessage.objects.get(topic=settings.METADB_NATS_REQUEST_UPDATE)
        self.assertEqual(smile_msg.request_id, "10075_D")
        self.assertEqual(smile_msg.gene_panel, "IMPACT468")
        self.assertEqual(smile_msg.status, SmileMessageStatus.PENDING)

    def test_persist_sample_update_message(self):
        """Test persisting a SAMPLE_UPDATE message extracts request_id and gene_panel from latestSampleMetadata."""
        # Create mock NATS message with sample update structure
        message_data = {
            "smileSampleId": "5fe2dc20-92f4-4763-b437-fa1e2fb1b93f",
            "primarySampleAlias": "10075_D_2",
            "sampleClass": "Normal",
            "datasource": "igo",
            "latestSampleMetadata": {
                "primaryId": "10075_D_2",
                settings.REQUEST_ID_METADATA_KEY: "10075_D",
                settings.RECIPE_METADATA_KEY: "GENESET101_BAITS",
                "cmoPatientId": "C-TEST001",
                "sampleName": "TestSample001",
                "igoComplete": True,
            },
        }

        message = Mock()
        message.subject = settings.METADB_NATS_SAMPLE_UPDATE
        message.data = json.dumps(message_data)

        # Call persist_message
        persist_message(message)

        # Verify SMILEMessage was created correctly
        smile_msg = SMILEMessage.objects.get(topic=settings.METADB_NATS_SAMPLE_UPDATE)
        self.assertEqual(smile_msg.request_id, "10075_D")
        self.assertEqual(smile_msg.gene_panel, "GENESET101_BAITS")
        self.assertEqual(smile_msg.status, SmileMessageStatus.PENDING)
        self.assertEqual(smile_msg.message, message.data)

    def test_persist_message_with_missing_request_id(self):
        """Test that persist_message catches exception when request_id is missing (.get returns None)."""
        from unittest.mock import patch

        message_data = {settings.RECIPE_METADATA_KEY: "IMPACT468", "labHeadName": "Test Researcher"}

        message = Mock()
        message.subject = settings.METADB_NATS_NEW_REQUEST
        message.data = json.dumps(message_data)

        # Mock the logger to verify error was logged
        with patch("beagle_etl.smile_service.smile_callback.logger") as mock_logger:
            # Call persist_message - will catch IntegrityError and log it
            persist_message(message)

            # Verify error was logged (indicating exception was caught gracefully)
            self.assertTrue(mock_logger.error.called)

    def test_persist_message_with_missing_gene_panel(self):
        """Test that persist_message handles missing gene_panel gracefully."""
        message_data = {settings.REQUEST_ID_METADATA_KEY: "08944_B", "labHeadName": "Test Researcher"}

        message = Mock()
        message.subject = settings.METADB_NATS_NEW_REQUEST
        message.data = json.dumps(message_data)

        # Call persist_message - should not raise exception
        persist_message(message)

        # Verify SMILEMessage was created with None gene_panel
        smile_msg = SMILEMessage.objects.get(topic=settings.METADB_NATS_NEW_REQUEST)
        self.assertEqual(smile_msg.request_id, "08944_B")
        self.assertIsNone(smile_msg.gene_panel)

    def test_persist_message_with_invalid_json(self):
        """Test that persist_message handles invalid JSON gracefully."""
        message = Mock()
        message.subject = settings.METADB_NATS_NEW_REQUEST
        message.data = "invalid json {{{}"

        # Call persist_message - catches JSON error and logs it
        persist_message(message)

        # Verify SMILEMessage WAS created with the raw data but empty request_id
        # (message is created first, then JSON parsing fails, leaving request_id empty)
        smile_msg = SMILEMessage.objects.get(topic=settings.METADB_NATS_NEW_REQUEST)
        self.assertEqual(smile_msg.message, "invalid json {{{}")
        self.assertEqual(smile_msg.request_id, "")  # Empty due to parsing failure
        self.assertIsNone(smile_msg.gene_panel)

    def test_persist_message_with_unknown_topic(self):
        """Test that persist_message handles unknown topics gracefully."""
        message_data = {settings.REQUEST_ID_METADATA_KEY: "08944_B", settings.RECIPE_METADATA_KEY: "IMPACT468"}

        message = Mock()
        message.subject = "UNKNOWN.TOPIC"
        message.data = json.dumps(message_data)

        # Call persist_message - should not crash
        persist_message(message)

        # Verify SMILEMessage WAS created with raw message
        # but request_id/gene_panel not extracted since topic doesn't match any known pattern
        smile_msg = SMILEMessage.objects.get(topic="UNKNOWN.TOPIC")
        self.assertEqual(smile_msg.message, message.data)
        self.assertEqual(smile_msg.request_id, "")  # Empty since no extraction logic for unknown topic
        self.assertIsNone(smile_msg.gene_panel)

    def test_persist_sample_update_without_latest_metadata(self):
        """Test that SAMPLE_UPDATE without latestSampleMetadata is handled gracefully."""
        message_data = {"smileSampleId": "5fe2dc20-92f4-4763-b437-fa1e2fb1b93f", "primarySampleAlias": "10075_D_2"}

        message = Mock()
        message.subject = settings.METADB_NATS_SAMPLE_UPDATE
        message.data = json.dumps(message_data)

        # Call persist_message - catches KeyError and logs error
        persist_message(message)

        # Verify SMILEMessage WAS created with raw data but empty request_id
        # (message created first, then Key Error on latestSampleMetadata, leaving request_id empty)
        smile_msg = SMILEMessage.objects.get(topic=settings.METADB_NATS_SAMPLE_UPDATE)
        self.assertEqual(smile_msg.message, message.data)
        self.assertEqual(smile_msg.request_id, "")  # Empty due to KeyError
        self.assertIsNone(smile_msg.gene_panel)

    def test_persist_message_creates_pending_status(self):
        """Test that all persisted messages start with PENDING status."""
        message_data = {settings.REQUEST_ID_METADATA_KEY: "08944_B", settings.RECIPE_METADATA_KEY: "IMPACT468"}

        for topic in [
            settings.METADB_NATS_NEW_REQUEST,
            settings.METADB_NATS_REQUEST_UPDATE,
            settings.METADB_NATS_SAMPLE_UPDATE,
        ]:
            message = Mock()
            message.subject = topic

            # Different formats for different topics
            if topic == settings.METADB_NATS_SAMPLE_UPDATE:
                data = {"latestSampleMetadata": message_data}
            elif topic == settings.METADB_NATS_REQUEST_UPDATE:
                # REQUEST_UPDATE is an array
                data = [
                    {
                        settings.REQUEST_ID_METADATA_KEY: message_data[settings.REQUEST_ID_METADATA_KEY],
                        "requestMetadataJson": json.dumps(message_data),
                    }
                ]
            else:
                data = message_data

            message.data = json.dumps(data)

            persist_message(message)

            smile_msg = SMILEMessage.objects.get(topic=topic)
            self.assertEqual(smile_msg.status, SmileMessageStatus.PENDING)

    def test_persist_multiple_messages_same_request(self):
        """Test persisting multiple messages for the same request_id."""
        request_id = "08944_B"

        # Create NEW_REQUEST message
        new_request_data = {settings.REQUEST_ID_METADATA_KEY: request_id, settings.RECIPE_METADATA_KEY: "IMPACT468"}
        message1 = Mock()
        message1.subject = settings.METADB_NATS_NEW_REQUEST
        message1.data = json.dumps(new_request_data)
        persist_message(message1)

        # Create REQUEST_UPDATE message (array format)
        update_request_data = [
            {
                settings.REQUEST_ID_METADATA_KEY: request_id,
                "requestMetadataJson": json.dumps({settings.RECIPE_METADATA_KEY: "IMPACT468"}),
            }
        ]
        message2 = Mock()
        message2.subject = settings.METADB_NATS_REQUEST_UPDATE
        message2.data = json.dumps(update_request_data)
        persist_message(message2)

        # Create SAMPLE_UPDATE message
        sample_update_data = {
            "latestSampleMetadata": {
                settings.REQUEST_ID_METADATA_KEY: request_id,
                settings.RECIPE_METADATA_KEY: "IMPACT468",
            }
        }
        message3 = Mock()
        message3.subject = settings.METADB_NATS_SAMPLE_UPDATE
        message3.data = json.dumps(sample_update_data)
        persist_message(message3)

        # Verify all three messages were created
        messages = SMILEMessage.objects.filter(request_id=request_id)
        self.assertEqual(messages.count(), 3)

        # Verify each topic exists
        topics = set(msg.topic for msg in messages)
        self.assertIn(settings.METADB_NATS_NEW_REQUEST, topics)
        self.assertIn(settings.METADB_NATS_REQUEST_UPDATE, topics)
        self.assertIn(settings.METADB_NATS_SAMPLE_UPDATE, topics)

    def test_persist_real_world_sample_update(self):
        """Test persisting a real-world sample update message with full structure."""
        # Real sample-update message with anonymized IDs
        message_data = {
            "smileSampleId": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
            "sampleClass": "Tumor",
            "sampleCategory": "research",
            "datasource": "igo",
            "revisable": True,
            "primarySampleAlias": "12345_AB_2",
            "latestSampleMetadata": {
                "primaryId": "12345_AB_2",
                "cmoPatientId": "C-TESTPT1",
                "investigatorSampleId": "TEST_SAMPLE_s_C_TESTPT1_X001_d01",
                "cmoSampleName": "C-TESTPT1-X001-d01",
                "sampleName": "TEST_SAMPLE_s_C_TESTPT1_X001_d01",
                settings.REQUEST_ID_METADATA_KEY: "12345_AB",
                "importDate": "2026-02-17",
                "oncotreeCode": "COADREAD",
                "species": "Human",
                "sex": "Female",
                "tumorOrNormal": "Tumor",
                "sampleType": "Primary",
                "preservation": "Frozen",
                "sampleClass": "PDX",
                settings.RECIPE_METADATA_KEY: "WGS_Shallow",
                "baitSet": "null",
                "igoComplete": True,
            },
        }

        message = Mock()
        message.subject = settings.METADB_NATS_SAMPLE_UPDATE
        message.data = json.dumps(message_data)

        # Call persist_message
        persist_message(message)

        # Verify SMILEMessage was created correctly
        smile_msg = SMILEMessage.objects.get(topic=settings.METADB_NATS_SAMPLE_UPDATE)
        self.assertEqual(smile_msg.request_id, "12345_AB")
        self.assertEqual(smile_msg.gene_panel, "WGS_Shallow")
        self.assertEqual(smile_msg.status, SmileMessageStatus.PENDING)

        # Verify the full message was stored
        stored_data = json.loads(smile_msg.message)
        self.assertEqual(stored_data["datasource"], "igo")
        self.assertEqual(stored_data["sampleClass"], "Tumor")
        self.assertEqual(stored_data["primarySampleAlias"], "12345_AB_2")

    def test_persist_real_world_request_update(self):
        """Test persisting a real-world request update message with array structure."""
        # Real request-update message with anonymized IDs (array of 2 updates)
        message_data = [
            {
                settings.REQUEST_ID_METADATA_KEY: "12345_AB",
                "requestMetadataJson": json.dumps(
                    {
                        "requestId": "12345_AB",
                        "requestName": "WholeGenome",
                        settings.RECIPE_METADATA_KEY: "WGS_Shallow",
                        "labHeadName": "Test Lab Head",
                        "labHeadEmail": "labhead@example.org",
                        "investigatorName": "Test Investigator",
                        "investigatorEmail": "investigator@example.org",
                        "isCmoRequest": True,
                        "bicAnalysis": True,
                        "deliveryPath": "/ifs/datadelivery/igo_core/share/testuser",
                        "projectId": "12345",
                        "status": {"validationReport": "{}", "validationStatus": True},
                    }
                ),
                "importDate": "2026-02-17",
                "status": {"validationStatus": True, "validationReport": "{}"},
            },
            {
                settings.REQUEST_ID_METADATA_KEY: "12345_AB",
                "requestMetadataJson": json.dumps(
                    {
                        "requestId": "12345_AB",
                        "requestName": "WholeGenome",
                        settings.RECIPE_METADATA_KEY: "WGS_Shallow",
                        "labHeadName": "Test Lab Head",
                        "investigatorName": "Test Investigator",
                        "projectId": "12345",
                    }
                ),
                "importDate": "2026-02-17",
            },
        ]

        message = Mock()
        message.subject = settings.METADB_NATS_REQUEST_UPDATE
        message.data = json.dumps(message_data)

        # Call persist_message
        persist_message(message)

        # Verify SMILEMessage was created correctly
        smile_msg = SMILEMessage.objects.get(topic=settings.METADB_NATS_REQUEST_UPDATE)
        self.assertEqual(smile_msg.request_id, "12345_AB")
        self.assertEqual(smile_msg.gene_panel, "WGS_Shallow")
        self.assertEqual(smile_msg.status, SmileMessageStatus.PENDING)

        # Verify the full array was stored
        stored_data = json.loads(smile_msg.message)
        self.assertTrue(isinstance(stored_data, list))
        self.assertEqual(len(stored_data), 2)
        self.assertEqual(stored_data[0][settings.REQUEST_ID_METADATA_KEY], "12345_AB")
