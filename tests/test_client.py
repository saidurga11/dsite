"""Tests for Pulse SDK client."""

import pytest

from pulse import AirflowContext, MockQueueAdapter, PulseClient
from pulse.exceptions import ConfigurationError, ValidationError


class TestPulseClientInit:
    """Tests for PulseClient initialization."""

    def test_init_with_valid_service_and_context(
        self,
        sample_airflow_context: AirflowContext,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test initializing with valid service and context."""
        client = PulseClient(
            service="leverage",
            airflow_context=sample_airflow_context,
            queue_adapter=mock_queue_adapter,
        )

        assert client is not None

    def test_init_with_empty_service_name(
        self,
        sample_airflow_context: AirflowContext,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that empty service name raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            PulseClient(
                service="",
                airflow_context=sample_airflow_context,
                queue_adapter=mock_queue_adapter,
            )

        assert "cannot be empty" in str(exc_info.value)

    def test_init_with_nonexistent_service(
        self,
        sample_airflow_context: AirflowContext,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that non-existent service raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            PulseClient(
                service="nonexistent",
                airflow_context=sample_airflow_context,
                queue_adapter=mock_queue_adapter,
            )

        assert "not registered" in str(exc_info.value)

    def test_init_with_none_airflow_context(
        self,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that None airflow_context raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            PulseClient(
                service="leverage",
                airflow_context=None,  # type: ignore
                queue_adapter=mock_queue_adapter,
            )

        assert "cannot be None" in str(exc_info.value)

    def test_init_with_invalid_airflow_context_type(
        self,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that invalid airflow_context type raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            PulseClient(
                service="leverage",
                airflow_context={"dag_id": "dag", "task_id": "task", "run_id": "run"},  # type: ignore
                queue_adapter=mock_queue_adapter,
            )

        assert "must be an AirflowContext instance" in str(exc_info.value)

    def test_init_with_empty_dag_id(
        self,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that empty dag_id raises ConfigurationError."""
        context = AirflowContext(dag_id="", task_id="task", run_id="run")

        with pytest.raises(ConfigurationError) as exc_info:
            PulseClient(
                service="leverage",
                airflow_context=context,
                queue_adapter=mock_queue_adapter,
            )

        assert "dag_id cannot be empty" in str(exc_info.value)

    def test_init_with_empty_task_id(
        self,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that empty task_id raises ConfigurationError."""
        context = AirflowContext(dag_id="dag", task_id="", run_id="run")

        with pytest.raises(ConfigurationError) as exc_info:
            PulseClient(
                service="leverage",
                airflow_context=context,
                queue_adapter=mock_queue_adapter,
            )

        assert "task_id cannot be empty" in str(exc_info.value)

    def test_init_with_empty_run_id(
        self,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that empty run_id raises ConfigurationError."""
        context = AirflowContext(dag_id="dag", task_id="task", run_id="")

        with pytest.raises(ConfigurationError) as exc_info:
            PulseClient(
                service="leverage",
                airflow_context=context,
                queue_adapter=mock_queue_adapter,
            )

        assert "run_id cannot be empty" in str(exc_info.value)


class TestPulseClientEmit:
    """Tests for PulseClient.emit method."""

    @pytest.fixture
    def client(
        self,
        sample_airflow_context: AirflowContext,
        mock_queue_adapter: MockQueueAdapter,
    ) -> PulseClient:
        """Create a PulseClient for testing."""
        return PulseClient(
            service="leverage",
            airflow_context=sample_airflow_context,
            queue_adapter=mock_queue_adapter,
        )

    def test_emit_counter_with_dedup(
        self,
        client: PulseClient,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test emitting a counter metric with deduplication."""
        result = client.emit(
            metric_name="tagged",
            value=1,
            entity_id="tx_123",
        )

        assert result is True
        assert len(mock_queue_adapter.messages) == 1

        message = mock_queue_adapter.messages[0]
        assert message.metric_name == "tagged"
        assert message.value == 1.0
        assert message.entity_id == "tx_123"

    def test_emit_timing_without_dedup(
        self,
        client: PulseClient,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test emitting a timing metric without deduplication."""
        # Emit twice with same entity_id - both should succeed (no dedup)
        result1 = client.emit(
            metric_name="match_latency_ms",
            value=45.2,
            entity_id="tx_123",
        )
        result2 = client.emit(
            metric_name="match_latency_ms",
            value=50.5,
            entity_id="tx_123",
        )

        assert result1 is True
        assert result2 is True
        assert len(mock_queue_adapter.messages) == 2

    def test_emit_duplicate_rejected(
        self,
        client: PulseClient,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that duplicate emissions are rejected."""
        # First emit succeeds
        result1 = client.emit(
            metric_name="tagged",
            value=1,
            entity_id="tx_123",
        )
        assert result1 is True

        # Second emit with same entity_id is rejected
        result2 = client.emit(
            metric_name="tagged",
            value=1,
            entity_id="tx_123",
        )
        assert result2 is False

        # Only one message stored
        assert len(mock_queue_adapter.messages) == 1

    def test_emit_unregistered_metric_raises(
        self,
        client: PulseClient,
    ) -> None:
        """Test that emitting unregistered metric raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.emit(
                metric_name="unknown_metric",
                value=1,
                entity_id="tx_123",
            )

        assert "not registered" in str(exc_info.value)

    def test_emit_missing_entity_id_when_dedup_enabled(
        self,
        client: PulseClient,
    ) -> None:
        """Test that missing entity_id raises ValidationError when dedup enabled."""
        with pytest.raises(ValidationError) as exc_info:
            client.emit(
                metric_name="tagged",
                value=1,
                entity_id="",  # Empty
            )

        assert "cannot be empty" in str(exc_info.value)

    def test_emit_none_entity_id_when_dedup_enabled(
        self,
        client: PulseClient,
    ) -> None:
        """Test that None entity_id raises ValidationError when dedup enabled."""
        with pytest.raises(ValidationError) as exc_info:
            client.emit(
                metric_name="tagged",
                value=1,
                entity_id=None,  # type: ignore
            )

        assert "is required" in str(exc_info.value)

    def test_emit_invalid_value_raises(
        self,
        client: PulseClient,
    ) -> None:
        """Test that invalid value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.emit(
                metric_name="tagged",
                value="not a number",  # type: ignore
                entity_id="tx_123",
            )

        assert "must be numeric" in str(exc_info.value)

    def test_idempotency_key_format(
        self,
        client: PulseClient,
        mock_queue_adapter: MockQueueAdapter,
        sample_airflow_context: AirflowContext,
    ) -> None:
        """Test that idempotency key has correct format."""
        client.emit(
            metric_name="tagged",
            value=1,
            entity_id="tx_abc123",
        )

        message = mock_queue_adapter.messages[0]
        expected_key = (
            f"{sample_airflow_context.dag_id}_"
            f"{sample_airflow_context.task_id}_"
            f"{sample_airflow_context.run_id}_"
            "tagged_"
            "tx_abc123"
        )
        assert message.idempotency_key == expected_key


class TestPulseClientEmitBatch:
    """Tests for PulseClient.emit_batch method."""

    @pytest.fixture
    def client(
        self,
        sample_airflow_context: AirflowContext,
        mock_queue_adapter: MockQueueAdapter,
    ) -> PulseClient:
        """Create a PulseClient for testing."""
        return PulseClient(
            service="leverage",
            airflow_context=sample_airflow_context,
            queue_adapter=mock_queue_adapter,
        )

    def test_emit_batch_multiple_metrics(
        self,
        client: PulseClient,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test batch emitting multiple metrics."""
        metrics = [
            {"metric_name": "tagged", "value": 1, "entity_id": "tx_001"},
            {"metric_name": "tagged", "value": 1, "entity_id": "tx_002"},
            {"metric_name": "match_latency_ms", "value": 50.5, "entity_id": "tx_003"},
        ]

        result = client.emit_batch(metrics)

        assert result == 3
        assert len(mock_queue_adapter.messages) == 3

    def test_emit_batch_with_duplicates(
        self,
        client: PulseClient,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test batch emitting with duplicate entity_ids."""
        metrics = [
            {"metric_name": "tagged", "value": 1, "entity_id": "tx_001"},
            {"metric_name": "tagged", "value": 1, "entity_id": "tx_001"},  # Duplicate
            {"metric_name": "tagged", "value": 1, "entity_id": "tx_002"},
        ]

        result = client.emit_batch(metrics)

        assert result == 2  # Only 2 unique
        assert len(mock_queue_adapter.messages) == 2

    def test_emit_batch_validation_error_shows_index(
        self,
        client: PulseClient,
    ) -> None:
        """Test that validation errors show the metric index."""
        metrics = [
            {"metric_name": "tagged", "value": 1, "entity_id": "tx_001"},
            {"metric_name": "unknown_metric", "value": 1, "entity_id": "tx_002"},  # Invalid
            {"metric_name": "tagged", "value": 1, "entity_id": "tx_003"},
        ]

        with pytest.raises(ValidationError) as exc_info:
            client.emit_batch(metrics)

        assert "index 1" in str(exc_info.value)

    def test_emit_batch_empty_list(
        self,
        client: PulseClient,
    ) -> None:
        """Test batch emitting empty list."""
        result = client.emit_batch([])

        assert result == 0

    def test_emit_batch_missing_required_field_raises(
        self,
        client: PulseClient,
    ) -> None:
        """Test that missing required field raises ValidationError."""
        metrics = [
            {"metric_name": "tagged", "entity_id": "tx_001"},  # Missing value
        ]

        with pytest.raises(ValidationError) as exc_info:
            client.emit_batch(metrics)

        assert "value is required" in str(exc_info.value)

    def test_emit_batch_not_list_raises(
        self,
        client: PulseClient,
    ) -> None:
        """Test that non-list input raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.emit_batch("not a list")  # type: ignore

        assert "must be a list" in str(exc_info.value)

    def test_emit_batch_item_not_dict_raises(
        self,
        client: PulseClient,
    ) -> None:
        """Test that non-dict item raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            client.emit_batch(["not a dict"])  # type: ignore

        assert "index 0" in str(exc_info.value)
        assert "must be a dict" in str(exc_info.value)


class TestPulseClientIntegration:
    """Integration tests for PulseClient."""

    def test_full_workflow(
        self,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test a complete workflow with the leverage service."""
        context = AirflowContext(
            dag_id="leverage_tagging_dag",
            task_id="tag_transactions",
            run_id="scheduled__2026-01-08T14:00:00",
        )

        client = PulseClient(
            service="leverage",
            airflow_context=context,
            queue_adapter=mock_queue_adapter,
        )

        # Emit counter (with dedup)
        result1 = client.emit(
            metric_name="tagged",
            value=1,
            entity_id="tx_abc123",
        )
        assert result1 is True

        # Emit timing (no dedup)
        result2 = client.emit(
            metric_name="match_latency_ms",
            value=45.2,
            entity_id="tx_abc123",
        )
        assert result2 is True

        # Try duplicate counter - should be rejected
        result3 = client.emit(
            metric_name="tagged",
            value=1,
            entity_id="tx_abc123",
        )
        assert result3 is False

        # Verify messages
        assert len(mock_queue_adapter.messages) == 2

        # Verify counter message
        counter_msg = mock_queue_adapter.messages[0]
        assert counter_msg.metric_name == "tagged"
        assert counter_msg.value == 1.0

        # Verify timing message
        timing_msg = mock_queue_adapter.messages[1]
        assert timing_msg.metric_name == "match_latency_ms"
        assert timing_msg.value == 45.2

    def test_batch_workflow(
        self,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test batch emission workflow."""
        context = AirflowContext(
            dag_id="leverage_tagging_dag",
            task_id="tag_transactions",
            run_id="scheduled__2026-01-08T14:00:00",
        )

        client = PulseClient(
            service="leverage",
            airflow_context=context,
            queue_adapter=mock_queue_adapter,
        )

        metrics = [
            {"metric_name": "tagged", "value": 1, "entity_id": "tx_001"},
            {"metric_name": "tagged", "value": 1, "entity_id": "tx_002"},
            {"metric_name": "match_latency_ms", "value": 45.2, "entity_id": "tx_001"},
        ]

        result = client.emit_batch(metrics)

        assert result == 3
        assert len(mock_queue_adapter.messages) == 3
