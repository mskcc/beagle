"""
Tests for beagle_etl.tasks module
"""
from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from beagle_etl.models import SMILEMessage, SmileMessageStatus
from beagle_etl.tasks import get_pending_smile_messages
from datetime import timedelta


class TestGetPendingSmileMessages(TestCase):
    """Test that get_pending_smile_messages returns the highest priority message per request_id."""

    def setUp(self):
        """Create test messages with different topics and timestamps."""
        # Create a base time
        base_time = timezone.now()

        # Create messages for different request_ids to test basic functionality
        self.new_request_1 = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_NEW_REQUEST,
            request_id="REQ_001",
            message='{"test": "data1"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(hours=1),
        )

        self.new_request_2 = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_NEW_REQUEST,
            request_id="REQ_002",
            message='{"test": "data2"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(hours=3),
        )

        self.sample_update_1 = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_SAMPLE_UPDATE,
            request_id="REQ_003",
            message='{"test": "data3"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(hours=2),
        )

        self.sample_update_2 = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_SAMPLE_UPDATE,
            request_id="REQ_004",
            message='{"test": "data4"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(hours=5),
        )

        self.request_update_1 = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_REQUEST_UPDATE,
            request_id="REQ_005",
            message='{"test": "data5"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(hours=4),
        )

        self.request_update_2 = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_REQUEST_UPDATE,
            request_id="REQ_006",
            message='{"test": "data6"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(hours=6),
        )

    def test_one_message_per_request_id(self):
        """Test that only one message per request_id is returned (each test message has unique request_id)."""
        messages = get_pending_smile_messages()
        message_list = list(messages)

        # All 6 messages should be returned since they all have different request_ids
        self.assertEqual(len(message_list), 6)

        # Verify each request_id appears only once
        request_ids = [msg.request_id for msg in message_list]
        self.assertEqual(len(request_ids), len(set(request_ids)))

    def test_highest_priority_message_per_request(self):
        """Test that when a request has multiple pending messages, only the highest priority one is returned."""
        base_time = timezone.now()

        # Create multiple messages for the same request_id with different priorities
        # REQUEST_UPDATE (lowest priority) - created first
        update_msg = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_REQUEST_UPDATE,
            request_id="REQ_MULTI",
            message='{"test": "update"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time,
        )

        # SAMPLE_UPDATE (medium priority)
        sample_msg = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_SAMPLE_UPDATE,
            request_id="REQ_MULTI",
            message='{"test": "sample"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(minutes=1),
        )

        # NEW_REQUEST (highest priority)
        new_msg = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_NEW_REQUEST,
            request_id="REQ_MULTI",
            message='{"test": "new"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(minutes=2),
        )

        messages = get_pending_smile_messages()
        message_list = list(messages)

        # Should return 7 messages total (6 from setUp + 1 for REQ_MULTI)
        self.assertEqual(len(message_list), 7)

        # Find the message for REQ_MULTI
        multi_messages = [msg for msg in message_list if msg.request_id == "REQ_MULTI"]
        self.assertEqual(len(multi_messages), 1, "Should return exactly one message for REQ_MULTI")

        # Verify it's the NEW_REQUEST message (highest priority)
        self.assertEqual(multi_messages[0].id, new_msg.id)
        self.assertEqual(multi_messages[0].topic, settings.METADB_NATS_NEW_REQUEST)

    def test_priority_order_with_same_request(self):
        """Test NEW_REQUEST > SAMPLE_UPDATE > REQUEST_UPDATE priority for the same request_id."""
        base_time = timezone.now()

        # Test 1: Only REQUEST_UPDATE and SAMPLE_UPDATE pending
        SMILEMessage.objects.create(
            topic=settings.METADB_NATS_REQUEST_UPDATE,
            request_id="REQ_TEST1",
            message='{"test": "update"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time,
        )
        sample_update = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_SAMPLE_UPDATE,
            request_id="REQ_TEST1",
            message='{"test": "sample"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(minutes=1),
        )

        messages = get_pending_smile_messages()
        test1_messages = [msg for msg in messages if msg.request_id == "REQ_TEST1"]
        self.assertEqual(len(test1_messages), 1)
        self.assertEqual(test1_messages[0].id, sample_update.id)

    def test_earliest_message_when_same_priority(self):
        """Test that when multiple messages have the same priority, the earliest is returned."""
        base_time = timezone.now()

        # Create two NEW_REQUEST messages for the same request_id
        early_msg = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_NEW_REQUEST,
            request_id="REQ_SAME_PRIORITY",
            message='{"test": "early"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time,
        )

        late_msg = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_NEW_REQUEST,
            request_id="REQ_SAME_PRIORITY",
            message='{"test": "late"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(hours=1),
        )

        messages = get_pending_smile_messages()
        same_priority_messages = [msg for msg in messages if msg.request_id == "REQ_SAME_PRIORITY"]

        self.assertEqual(len(same_priority_messages), 1)
        self.assertEqual(same_priority_messages[0].id, early_msg.id)

    def test_only_pending_messages_included(self):
        """Test that only PENDING messages are included in the query."""
        base_time = timezone.now()

        # Create a completed NEW_REQUEST message for a request that also has pending messages
        SMILEMessage.objects.create(
            topic=settings.METADB_NATS_NEW_REQUEST,
            request_id="REQ_COMPLETED_TEST",
            message='{"test": "completed"}',
            status=SmileMessageStatus.COMPLETED,
            created_date=base_time,
        )

        # Create a pending REQUEST_UPDATE for the same request
        pending_msg = SMILEMessage.objects.create(
            topic=settings.METADB_NATS_REQUEST_UPDATE,
            request_id="REQ_COMPLETED_TEST",
            message='{"test": "pending"}',
            status=SmileMessageStatus.PENDING,
            created_date=base_time + timedelta(minutes=1),
        )

        messages = get_pending_smile_messages()
        message_list = list(messages)

        # Should return the pending REQUEST_UPDATE, not the completed NEW_REQUEST
        completed_test_messages = [msg for msg in message_list if msg.request_id == "REQ_COMPLETED_TEST"]
        self.assertEqual(len(completed_test_messages), 1)
        self.assertEqual(completed_test_messages[0].id, pending_msg.id)
        self.assertEqual(completed_test_messages[0].status, SmileMessageStatus.PENDING)
