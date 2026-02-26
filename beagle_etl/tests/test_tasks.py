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
    """Test that get_pending_smile_messages returns messages in the correct order."""

    def setUp(self):
        """Create test messages with different topics and timestamps."""
        # Create a base time
        base_time = timezone.now()

        # Create messages with different topics and timestamps
        # The order should be: NEW_REQUEST (by date), SAMPLE_UPDATE (by date), REQUEST_UPDATE (by date)

        # Create NEW_REQUEST messages
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

        # Create SAMPLE_UPDATE messages
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

        # Create REQUEST_UPDATE messages
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

    def test_message_ordering(self):
        """Test that messages are retrieved in the correct order: NEW_REQUEST, SAMPLE_UPDATE, REQUEST_UPDATE, each sorted by date."""
        # Call the function
        messages = get_pending_smile_messages()

        # Convert to list to check order
        message_list = list(messages)

        # Assert we have all 6 messages
        self.assertEqual(len(message_list), 6)

        # Expected order:
        # 1. new_request_1 (NEW_REQUEST, hour 1)
        # 2. new_request_2 (NEW_REQUEST, hour 3)
        # 3. sample_update_1 (SAMPLE_UPDATE, hour 2)
        # 4. sample_update_2 (SAMPLE_UPDATE, hour 5)
        # 5. request_update_1 (REQUEST_UPDATE, hour 4)
        # 6. request_update_2 (REQUEST_UPDATE, hour 6)

        self.assertEqual(message_list[0].id, self.new_request_1.id)
        self.assertEqual(message_list[0].topic, settings.METADB_NATS_NEW_REQUEST)

        self.assertEqual(message_list[1].id, self.new_request_2.id)
        self.assertEqual(message_list[1].topic, settings.METADB_NATS_NEW_REQUEST)

        self.assertEqual(message_list[2].id, self.sample_update_1.id)
        self.assertEqual(message_list[2].topic, settings.METADB_NATS_SAMPLE_UPDATE)

        self.assertEqual(message_list[3].id, self.sample_update_2.id)
        self.assertEqual(message_list[3].topic, settings.METADB_NATS_SAMPLE_UPDATE)

        self.assertEqual(message_list[4].id, self.request_update_1.id)
        self.assertEqual(message_list[4].topic, settings.METADB_NATS_REQUEST_UPDATE)

        self.assertEqual(message_list[5].id, self.request_update_2.id)
        self.assertEqual(message_list[5].topic, settings.METADB_NATS_REQUEST_UPDATE)

    def test_topic_priority_groups(self):
        """Test that all NEW_REQUEST messages come before SAMPLE_UPDATE, and all SAMPLE_UPDATE before REQUEST_UPDATE."""
        messages = get_pending_smile_messages()

        # Track which topic group we're in
        previous_priority = -1

        for msg in messages:
            if msg.topic == settings.METADB_NATS_NEW_REQUEST:
                current_priority = 0
            elif msg.topic == settings.METADB_NATS_SAMPLE_UPDATE:
                current_priority = 1
            elif msg.topic == settings.METADB_NATS_REQUEST_UPDATE:
                current_priority = 2
            else:
                current_priority = 3

            # Current priority should never be less than previous
            # (we should never go backwards in topic groups)
            self.assertGreaterEqual(
                current_priority,
                previous_priority,
                f"Topic priority went backwards: {previous_priority} -> {current_priority}",
            )
            previous_priority = current_priority

    def test_within_topic_date_ordering(self):
        """Test that within each topic group, messages are ordered by created_date."""
        messages = get_pending_smile_messages()

        # Group messages by topic
        topic_groups = {}
        for msg in messages:
            if msg.topic not in topic_groups:
                topic_groups[msg.topic] = []
            topic_groups[msg.topic].append(msg)

        # Check that within each topic, messages are ordered by date
        for topic, msgs in topic_groups.items():
            previous_date = None
            for msg in msgs:
                if previous_date is not None:
                    self.assertGreaterEqual(
                        msg.created_date, previous_date, f"Messages within topic {topic} are not ordered by date"
                    )
                previous_date = msg.created_date

    def test_only_pending_messages_included(self):
        """Test that only PENDING messages are included in the query."""
        # Create a completed message
        SMILEMessage.objects.create(
            topic=settings.METADB_NATS_NEW_REQUEST,
            request_id="REQ_COMPLETED",
            message='{"test": "completed"}',
            status=SmileMessageStatus.COMPLETED,
            created_date=timezone.now(),
        )

        messages = get_pending_smile_messages()

        # Should still only have 6 PENDING messages
        self.assertEqual(messages.count(), 6)

        # Verify none are completed
        for msg in messages:
            self.assertEqual(msg.status, SmileMessageStatus.PENDING)
