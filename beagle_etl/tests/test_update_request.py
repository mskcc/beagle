import json
from django.test import TestCase
from beagle_etl.smile_message.objects.update_request import UpdateRequest, UpdateRequestMetadata


class TestUpdateRequestDeserialization(TestCase):
    def setUp(self):
        """Set up test data with anonymized JSON."""
        self.json_data = [
            {
                "igoRequestId": "12345_BH",
                "requestMetadataJson": json.dumps(
                    {
                        "requestId": "12345_BH",
                        "requestName": "WholeGenome",
                        "recipe": "WGS_Shallow",
                        "projectManagerName": "",
                        "piEmail": "",
                        "labHeadName": "Test Researcher",
                        "labHeadEmail": "researcher@example.org",
                        "investigatorName": "Test Investigator",
                        "investigatorEmail": "investigator@example.org",
                        "dataAnalystName": "",
                        "dataAnalystEmail": "",
                        "otherContactEmails": "researcher@example.org",
                        "dataAccessEmails": "researcher@example.org",
                        "qcAccessEmails": "researcher@example.org",
                        "strand": None,
                        "libraryType": None,
                        "isCmoRequest": True,
                        "bicAnalysis": True,
                        "neoAg": False,
                        "deliveryDate": 1771290987386,
                        "deliveryPath": "/ifs/datadelivery/igo_core/share/test_user",
                        "pooledNormals": None,
                        "projectId": "12345",
                        "status": {"validationReport": "{}", "validationStatus": True},
                    }
                ),
                "importDate": "2026-02-17",
                "status": {"validationStatus": True, "validationReport": "{}"},
            },
            {
                "igoRequestId": "12345_BH",
                "requestMetadataJson": json.dumps(
                    {
                        "ilabRequestId": "",
                        "requestId": "12345_BH",
                        "requestName": "WholeGenome",
                        "recipe": "WGS_Shallow",
                        "projectManagerName": "",
                        "piEmail": "",
                        "labHeadName": "Test Researcher",
                        "labHeadEmail": "researcher@example.org",
                        "investigatorName": "Test Investigator",
                        "investigatorEmail": "investigator@example.org",
                        "dataAnalystName": "",
                        "dataAnalystEmail": "",
                        "otherContactEmails": "researcher@example.org",
                        "dataAccessEmails": "researcher@example.org",
                        "qcAccessEmails": "researcher@example.org",
                        "isCmoRequest": True,
                        "bicAnalysis": True,
                        "neoAg": False,
                        "deliveryPath": "/ifs/datadelivery/igo_core/share/test_user",
                        "projectId": "12345",
                        "status": {"validationReport": "{}", "validationStatus": True},
                    }
                ),
                "importDate": "2026-02-17",
                "status": {"validationStatus": True, "validationReport": "{}"},
            },
        ]

    def test_deserialize_update_request(self):
        """Test deserialization of list to UpdateRequest object."""
        update_request = UpdateRequest.from_list(self.json_data)

        # Assert that we have 2 updates
        self.assertEqual(len(update_request.updates), 2)

    def test_deserialize_update_request_metadata(self):
        """Test deserialization of individual update request metadata."""
        update_request = UpdateRequest.from_list(self.json_data)

        # Test first update
        update1 = update_request.updates[0]
        self.assertEqual(update1.igoRequestId, "12345_BH")
        self.assertEqual(update1.importDate, "2026-02-17")
        self.assertTrue(update1.status.validationStatus)
        self.assertEqual(update1.status.validationReport, "{}")

        # Test second update
        update2 = update_request.updates[1]
        self.assertEqual(update2.igoRequestId, "12345_BH")
        self.assertEqual(update2.importDate, "2026-02-17")
        self.assertTrue(update2.status.validationStatus)

    def test_deserialize_request_metadata_json(self):
        """Test that requestMetadataJson is properly stored as RequestMetadata object."""
        update_request = UpdateRequest.from_list(self.json_data)

        update1 = update_request.updates[0]
        self.assertIsNotNone(update1.requestMetadataJson)
        # Now it's a RequestMetadata object, not a string
        from beagle_etl.smile_message.objects.request_object import RequestMetadata

        self.assertIsInstance(update1.requestMetadataJson, RequestMetadata)

    def test_request_metadata_fields(self):
        """Test that RequestMetadata object has correct fields."""
        update_request = UpdateRequest.from_list(self.json_data)

        update1 = update_request.updates[0]
        request_metadata = update1.requestMetadataJson

        # Assert fields (note: requestId is renamed to igoRequestId, recipe to genePanel)
        self.assertEqual(request_metadata.igoRequestId, "12345_BH")
        self.assertEqual(request_metadata.genePanel, "WGS_Shallow")
        self.assertEqual(request_metadata.labHeadName, "Test Researcher")
        self.assertEqual(request_metadata.labHeadEmail, "researcher@example.org")
        self.assertEqual(request_metadata.investigatorName, "Test Investigator")
        self.assertEqual(request_metadata.investigatorEmail, "investigator@example.org")
        self.assertTrue(request_metadata.isCmoRequest)
        self.assertTrue(request_metadata.bicAnalysis)
        self.assertEqual(request_metadata.igoProjectId, "12345")
        # Note: deliveryDate is converted to igoDeliveryDate
        self.assertIsNotNone(request_metadata.igoDeliveryDate)

    def test_second_update_metadata(self):
        """Test requestMetadataJson for second update."""
        update_request = UpdateRequest.from_list(self.json_data)

        update2 = update_request.updates[1]
        request_metadata = update2.requestMetadataJson

        # Assert that second update has ilabRequestId field
        self.assertIsNotNone(request_metadata.ilabRequestId)
        self.assertEqual(request_metadata.ilabRequestId, "")
        self.assertEqual(request_metadata.igoRequestId, "12345_BH")

    def test_get_latest_update(self):
        """Test getting the latest update."""
        update_request = UpdateRequest.from_list(self.json_data)

        latest = update_request.get_latest_update()
        self.assertIsNotNone(latest)
        self.assertEqual(latest.igoRequestId, "12345_BH")

        # Verify it's the last item and has ilabRequestId
        self.assertIsNotNone(latest.requestMetadataJson.ilabRequestId)

    def test_get_latest_update_empty_list(self):
        """Test getting latest update from empty list."""
        update_request = UpdateRequest(updates=[])

        latest = update_request.get_latest_update()
        self.assertIsNone(latest)

    def test_get_updates_by_request_id(self):
        """Test filtering updates by request ID."""
        update_request = UpdateRequest.from_list(self.json_data)

        filtered = update_request.get_updates_by_request_id("12345_BH")
        self.assertEqual(len(filtered), 2)

        # Test with non-existent request ID
        filtered_empty = update_request.get_updates_by_request_id("99999_XX")
        self.assertEqual(len(filtered_empty), 0)

    def test_get_updates_by_request_id_mixed(self):
        """Test filtering with mixed request IDs."""
        # Add another request to the data
        mixed_data = self.json_data + [
            {
                "igoRequestId": "67890_AB",
                "requestMetadataJson": json.dumps(
                    {
                        "requestId": "67890_AB",
                        "requestName": "TestRequest",
                        "recipe": "IMPACT505",
                        "projectId": "67890",
                        "status": {"validationReport": "{}", "validationStatus": True},
                    }
                ),
                "importDate": "2026-02-18",
                "status": {"validationStatus": True, "validationReport": "{}"},
            }
        ]

        update_request = UpdateRequest.from_list(mixed_data)

        # Filter for first request
        filtered_first = update_request.get_updates_by_request_id("12345_BH")
        self.assertEqual(len(filtered_first), 2)

        # Filter for second request
        filtered_second = update_request.get_updates_by_request_id("67890_AB")
        self.assertEqual(len(filtered_second), 1)
        self.assertEqual(filtered_second[0].igoRequestId, "67890_AB")

    def test_to_list(self):
        """Test serialization back to list."""
        update_request = UpdateRequest.from_list(self.json_data)
        serialized = update_request.to_list()

        # Assert structure
        self.assertIsInstance(serialized, list)
        self.assertEqual(len(serialized), 2)

        # Assert first item
        self.assertEqual(serialized[0]["igoRequestId"], "12345_BH")
        self.assertEqual(serialized[0]["importDate"], "2026-02-17")
        self.assertIn("requestMetadataJson", serialized[0])
        self.assertIn("status", serialized[0])

    def test_to_dict_for_update_metadata(self):
        """Test to_dict on individual UpdateRequestMetadata."""
        update_request = UpdateRequest.from_list(self.json_data)
        update1 = update_request.updates[0]

        update_dict = update1.to_dict()

        self.assertEqual(update_dict["igoRequestId"], "12345_BH")
        self.assertEqual(update_dict["importDate"], "2026-02-17")
        self.assertIn("requestMetadataJson", update_dict)
        self.assertTrue(update_dict["status"]["validationStatus"])
        self.assertEqual(update_dict["status"]["validationReport"], "{}")

    def test_round_trip_serialization(self):
        """Test that data can be serialized and deserialized without loss."""
        update_request = UpdateRequest.from_list(self.json_data)
        serialized = update_request.to_list()

        # Deserialize again
        update_request2 = UpdateRequest.from_list(serialized)

        # Compare
        self.assertEqual(len(update_request.updates), len(update_request2.updates))
        self.assertEqual(update_request.updates[0].igoRequestId, update_request2.updates[0].igoRequestId)
        self.assertEqual(update_request.updates[0].importDate, update_request2.updates[0].importDate)

        # Compare request metadata fields
        metadata1 = update_request.updates[0].requestMetadataJson
        metadata2 = update_request2.updates[0].requestMetadataJson
        self.assertEqual(metadata1.igoRequestId, metadata2.igoRequestId)
        self.assertEqual(metadata1.genePanel, metadata2.genePanel)

    def test_status_deserialization(self):
        """Test that status is properly deserialized."""
        update_request = UpdateRequest.from_list(self.json_data)

        for update in update_request.updates:
            self.assertIsNotNone(update.status)
            self.assertTrue(update.status.validationStatus)
            self.assertEqual(update.status.validationReport, "{}")

    def test_empty_list_deserialization(self):
        """Test deserialization of empty list."""
        update_request = UpdateRequest.from_list([])

        self.assertEqual(len(update_request.updates), 0)
        self.assertIsNone(update_request.get_latest_update())

    def test_request_metadata_status_structure(self):
        """Test that requestMetadataJson has proper status structure."""
        update_request = UpdateRequest.from_list(self.json_data)

        update1 = update_request.updates[0]
        request_metadata = update1.requestMetadataJson

        # Verify nested status structure in RequestMetadata
        self.assertIsNotNone(request_metadata.status)
        self.assertIsNotNone(request_metadata.status.validationStatus)
        self.assertIsNotNone(request_metadata.status.validationReport)
        self.assertTrue(request_metadata.status.validationStatus)
