"""Tests for Pulse SDK queue adapters."""

import pytest

from pulse.models import MetricMessage
from pulse.queue_adapter import MockQueueAdapter


class TestMockQueueAdapter:
    """Tests for MockQueueAdapter."""

    @pytest.fixture
    def adapter(self) -> MockQueueAdapter:
        """Create a mock queue adapter."""
        return MockQueueAdapter()

    @pytest.fixture
    def sample_message(self) -> MetricMessage:
        """Create a sample metric message."""
        return MetricMessage(
            timestamp="2026-01-08T14:30:00Z",
            metric_name="tagged",
            value=1.0,
            entity_id="tx_abc123",
            idempotency_key="unique_key_1",
        )

    def test_enqueue_single_message(
        self,
        adapter: MockQueueAdapter,
        sample_message: MetricMessage,
    ) -> None:
        """Test enqueueing a single message."""
        result = adapter.enqueue(sample_message)

        assert result is True
        assert len(adapter.messages) == 1
        assert adapter.messages[0] == sample_message

    def test_enqueue_duplicate_rejected(
        self,
        adapter: MockQueueAdapter,
        sample_message: MetricMessage,
    ) -> None:
        """Test that duplicate messages are rejected."""
        # First enqueue succeeds
        result1 = adapter.enqueue(sample_message)
        assert result1 is True

        # Second enqueue with same key is rejected
        result2 = adapter.enqueue(sample_message)
        assert result2 is False

        # Only one message stored
        assert len(adapter.messages) == 1

        # Rejected key is tracked
        assert len(adapter.rejected_keys) == 1
        assert adapter.rejected_keys[0] == sample_message.idempotency_key

    def test_enqueue_different_keys_accepted(
        self,
        adapter: MockQueueAdapter,
    ) -> None:
        """Test that different keys are all accepted."""
        messages = [
            MetricMessage(
                timestamp="2026-01-08T14:30:00Z",
                metric_name="tagged",
                value=float(i),
                entity_id=f"tx_{i}",
                idempotency_key=f"key_{i}",
            )
            for i in range(5)
        ]

        for msg in messages:
            result = adapter.enqueue(msg)
            assert result is True

        assert len(adapter.messages) == 5

    def test_enqueue_batch_all_unique(
        self,
        adapter: MockQueueAdapter,
    ) -> None:
        """Test batch enqueue with all unique keys."""
        messages = [
            MetricMessage(
                timestamp="2026-01-08T14:30:00Z",
                metric_name="tagged",
                value=float(i),
                entity_id=f"tx_{i}",
                idempotency_key=f"key_{i}",
            )
            for i in range(3)
        ]

        result = adapter.enqueue_batch(messages)

        assert result == 3
        assert len(adapter.messages) == 3

    def test_enqueue_batch_with_duplicates(
        self,
        adapter: MockQueueAdapter,
    ) -> None:
        """Test batch enqueue with some duplicates."""
        # Pre-enqueue one message
        first_message = MetricMessage(
            timestamp="2026-01-08T14:30:00Z",
            metric_name="tagged",
            value=1.0,
            entity_id="tx_first",
            idempotency_key="existing_key",
        )
        adapter.enqueue(first_message)

        # Now batch with mix of new and duplicate
        messages = [
            MetricMessage(
                timestamp="2026-01-08T14:30:00Z",
                metric_name="tagged",
                value=2.0,
                entity_id="tx_new_1",
                idempotency_key="new_key_1",
            ),
            MetricMessage(
                timestamp="2026-01-08T14:30:00Z",
                metric_name="tagged",
                value=3.0,
                entity_id="tx_dup",
                idempotency_key="existing_key",  # Duplicate!
            ),
            MetricMessage(
                timestamp="2026-01-08T14:30:00Z",
                metric_name="tagged",
                value=4.0,
                entity_id="tx_new_2",
                idempotency_key="new_key_2",
            ),
        ]

        result = adapter.enqueue_batch(messages)

        assert result == 2  # Only 2 new messages accepted
        assert len(adapter.messages) == 3  # 1 original + 2 new
        assert len(adapter.rejected_keys) == 1

    def test_clear_resets_state(
        self,
        adapter: MockQueueAdapter,
        sample_message: MetricMessage,
    ) -> None:
        """Test that clear resets all state."""
        # Add some messages
        adapter.enqueue(sample_message)
        adapter.enqueue(sample_message)  # Will be rejected

        # Clear
        adapter.clear()

        # Everything should be reset
        assert len(adapter.messages) == 0
        assert len(adapter.rejected_keys) == 0
        assert len(adapter._seen_keys) == 0

        # Should be able to enqueue the same message again
        result = adapter.enqueue(sample_message)
        assert result is True

    def test_enqueue_batch_empty_list(
        self,
        adapter: MockQueueAdapter,
    ) -> None:
        """Test batch enqueue with empty list."""
        result = adapter.enqueue_batch([])

        assert result == 0
        assert len(adapter.messages) == 0

    def test_adapter_tracks_all_rejected_keys(
        self,
        adapter: MockQueueAdapter,
    ) -> None:
        """Test that adapter tracks all rejected duplicate keys."""
        message = MetricMessage(
            timestamp="2026-01-08T14:30:00Z",
            metric_name="tagged",
            value=1.0,
            entity_id="tx_123",
            idempotency_key="same_key",
        )

        # First succeeds
        adapter.enqueue(message)

        # Next 3 are rejected
        for _ in range(3):
            adapter.enqueue(message)

        assert len(adapter.rejected_keys) == 3
        assert all(k == "same_key" for k in adapter.rejected_keys)
