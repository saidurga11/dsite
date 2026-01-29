"""Tests for Pulse SDK client."""

import pytest

from pulse import AirflowContext, MockQueueAdapter, AggregationMonitoringService
from pulse.exceptions import ConfigurationError, ValidationError
from pulse.registry import LeverageMetrics, Metric


class TestAggregationMonitoringServiceInit:
    """Tests for AggregationMonitoringService initialization."""

    def test_init_with_valid_service_and_context(
        self,
        sample_airflow_context: AirflowContext,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test initializing with valid service and context."""
        service = AggregationMonitoringService(
            service="leverage",
            airflow_context=sample_airflow_context,
            queue_adapter=mock_queue_adapter,
        )

        assert service is not None

    def test_init_with_empty_service_name(
        self,
        sample_airflow_context: AirflowContext,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that empty service name raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AggregationMonitoringService(
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
            AggregationMonitoringService(
                service="nonexistent",
                airflow_context=sample_airflow_context,
                queue_adapter=mock_queue_adapter,
            )

        assert "not registered" in str(exc_info.value)

    def test_init_without_context_outside_airflow_raises(
        self,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that missing context outside Airflow raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            AggregationMonitoringService(
                service="leverage",
                queue_adapter=mock_queue_adapter,
            )

        assert "Airflow" in str(exc_info.value)

    def test_init_with_invalid_airflow_context_type(
        self,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that invalid airflow_context type raises ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            AggregationMonitoringService(
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
            AggregationMonitoringService(
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
            AggregationMonitoringService(
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
            AggregationMonitoringService(
                service="leverage",
                airflow_context=context,
                queue_adapter=mock_queue_adapter,
            )

        assert "run_id cannot be empty" in str(exc_info.value)


class TestAggregationMonitoringServiceRecordData:
    """Tests for AggregationMonitoringService.recordData method."""

    @pytest.fixture
    def service(
        self,
        sample_airflow_context: AirflowContext,
        mock_queue_adapter: MockQueueAdapter,
    ) -> AggregationMonitoringService:
        """Create an AggregationMonitoringService for testing."""
        return AggregationMonitoringService(
            service="leverage",
            airflow_context=sample_airflow_context,
            queue_adapter=mock_queue_adapter,
        )

    def test_record_counter_metric(
        self,
        service: AggregationMonitoringService,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test recording a counter metric."""
        result = service.recordData(
            metric=LeverageMetrics.TAGGED,
            value=1,
            entity_id="tx_123",
        )

        assert result is True
        assert len(mock_queue_adapter.messages) == 1

        message = mock_queue_adapter.messages[0]
        assert message.metric_name == "tagged"
        assert message.value == 1.0
        assert message.entity_id == "tx_123"

    def test_record_timing_metric(
        self,
        service: AggregationMonitoringService,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test recording a timing metric."""
        result = service.recordData(
            metric=LeverageMetrics.MATCH_LATENCY_MS,
            value=45.2,
            entity_id="tx_123",
        )

        assert result is True
        assert len(mock_queue_adapter.messages) == 1

        message = mock_queue_adapter.messages[0]
        assert message.metric_name == "match_latency_ms"
        assert message.value == 45.2

    def test_record_duplicate_rejected(
        self,
        service: AggregationMonitoringService,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test that duplicate recordings are rejected."""
        # First record succeeds
        result1 = service.recordData(
            metric=LeverageMetrics.TAGGED,
            value=1,
            entity_id="tx_123",
        )
        assert result1 is True

        # Second record with same entity_id is rejected
        result2 = service.recordData(
            metric=LeverageMetrics.TAGGED,
            value=1,
            entity_id="tx_123",
        )
        assert result2 is False

        # Only one message stored
        assert len(mock_queue_adapter.messages) == 1

    def test_record_unregistered_metric_raises(
        self,
        service: AggregationMonitoringService,
    ) -> None:
        """Test that recording unregistered metric raises ValidationError."""
        unregistered_metric = Metric(name="unknown_metric")
        with pytest.raises(ValidationError) as exc_info:
            service.recordData(
                metric=unregistered_metric,
                value=1,
                entity_id="tx_123",
            )

        assert "not registered" in str(exc_info.value)

    def test_record_empty_entity_id_raises(
        self,
        service: AggregationMonitoringService,
    ) -> None:
        """Test that empty entity_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            service.recordData(
                metric=LeverageMetrics.TAGGED,
                value=1,
                entity_id="",
            )

        assert "cannot be empty" in str(exc_info.value)

    def test_record_none_entity_id_raises(
        self,
        service: AggregationMonitoringService,
    ) -> None:
        """Test that None entity_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            service.recordData(
                metric=LeverageMetrics.TAGGED,
                value=1,
                entity_id=None,  # type: ignore
            )

        assert "is required" in str(exc_info.value)

    def test_record_invalid_value_raises(
        self,
        service: AggregationMonitoringService,
    ) -> None:
        """Test that invalid value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            service.recordData(
                metric=LeverageMetrics.TAGGED,
                value="not a number",  # type: ignore
                entity_id="tx_123",
            )

        assert "must be numeric" in str(exc_info.value)

    def test_idempotency_key_format(
        self,
        service: AggregationMonitoringService,
        mock_queue_adapter: MockQueueAdapter,
        sample_airflow_context: AirflowContext,
    ) -> None:
        """Test that idempotency key has correct format."""
        service.recordData(
            metric=LeverageMetrics.TAGGED,
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


class TestAggregationMonitoringServiceRecordDataBatch:
    """Tests for AggregationMonitoringService.recordDataBatch method."""

    @pytest.fixture
    def service(
        self,
        sample_airflow_context: AirflowContext,
        mock_queue_adapter: MockQueueAdapter,
    ) -> AggregationMonitoringService:
        """Create an AggregationMonitoringService for testing."""
        return AggregationMonitoringService(
            service="leverage",
            airflow_context=sample_airflow_context,
            queue_adapter=mock_queue_adapter,
        )

    def test_record_batch_multiple_metrics(
        self,
        service: AggregationMonitoringService,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test batch recording multiple metrics."""
        metrics = [
            {"metric": LeverageMetrics.TAGGED, "value": 1, "entity_id": "tx_001"},
            {"metric": LeverageMetrics.TAGGED, "value": 1, "entity_id": "tx_002"},
            {"metric": LeverageMetrics.MATCH_LATENCY_MS, "value": 50.5, "entity_id": "tx_003"},
        ]

        result = service.recordDataBatch(metrics)

        assert result == 3
        assert len(mock_queue_adapter.messages) == 3

    def test_record_batch_with_duplicates(
        self,
        service: AggregationMonitoringService,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test batch recording with duplicate entity_ids."""
        metrics = [
            {"metric": LeverageMetrics.TAGGED, "value": 1, "entity_id": "tx_001"},
            {"metric": LeverageMetrics.TAGGED, "value": 1, "entity_id": "tx_001"},  # Duplicate
            {"metric": LeverageMetrics.TAGGED, "value": 1, "entity_id": "tx_002"},
        ]

        result = service.recordDataBatch(metrics)

        assert result == 2  # Only 2 unique
        assert len(mock_queue_adapter.messages) == 2

    def test_record_batch_validation_error_shows_index(
        self,
        service: AggregationMonitoringService,
    ) -> None:
        """Test that validation errors show the metric index."""
        unregistered_metric = Metric(name="unknown_metric")
        metrics = [
            {"metric": LeverageMetrics.TAGGED, "value": 1, "entity_id": "tx_001"},
            {"metric": unregistered_metric, "value": 1, "entity_id": "tx_002"},  # Invalid
            {"metric": LeverageMetrics.TAGGED, "value": 1, "entity_id": "tx_003"},
        ]

        with pytest.raises(ValidationError) as exc_info:
            service.recordDataBatch(metrics)

        assert "index 1" in str(exc_info.value)

    def test_record_batch_empty_list(
        self,
        service: AggregationMonitoringService,
    ) -> None:
        """Test batch recording empty list."""
        result = service.recordDataBatch([])

        assert result == 0

    def test_record_batch_missing_required_field_raises(
        self,
        service: AggregationMonitoringService,
    ) -> None:
        """Test that missing required field raises ValidationError."""
        metrics = [
            {"metric": LeverageMetrics.TAGGED, "entity_id": "tx_001"},  # Missing value
        ]

        with pytest.raises(ValidationError) as exc_info:
            service.recordDataBatch(metrics)

        assert "value is required" in str(exc_info.value)

    def test_record_batch_not_list_raises(
        self,
        service: AggregationMonitoringService,
    ) -> None:
        """Test that non-list input raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            service.recordDataBatch("not a list")  # type: ignore

        assert "must be a list" in str(exc_info.value)

    def test_record_batch_item_not_dict_raises(
        self,
        service: AggregationMonitoringService,
    ) -> None:
        """Test that non-dict item raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            service.recordDataBatch(["not a dict"])  # type: ignore

        assert "index 0" in str(exc_info.value)
        assert "must be a dict" in str(exc_info.value)


class TestAggregationMonitoringServiceIntegration:
    """Integration tests for AggregationMonitoringService."""

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

        service = AggregationMonitoringService(
            service="leverage",
            airflow_context=context,
            queue_adapter=mock_queue_adapter,
        )

        # Record first metric
        result1 = service.recordData(
            metric=LeverageMetrics.TAGGED,
            value=1,
            entity_id="tx_abc123",
        )
        assert result1 is True

        # Record second metric
        result2 = service.recordData(
            metric=LeverageMetrics.MATCH_LATENCY_MS,
            value=45.2,
            entity_id="tx_def456",
        )
        assert result2 is True

        # Try duplicate - should be rejected
        result3 = service.recordData(
            metric=LeverageMetrics.TAGGED,
            value=1,
            entity_id="tx_abc123",
        )
        assert result3 is False

        # Verify messages
        assert len(mock_queue_adapter.messages) == 2

    def test_batch_workflow(
        self,
        mock_queue_adapter: MockQueueAdapter,
    ) -> None:
        """Test batch recording workflow."""
        context = AirflowContext(
            dag_id="leverage_tagging_dag",
            task_id="tag_transactions",
            run_id="scheduled__2026-01-08T14:00:00",
        )

        service = AggregationMonitoringService(
            service="leverage",
            airflow_context=context,
            queue_adapter=mock_queue_adapter,
        )

        metrics = [
            {"metric": LeverageMetrics.TAGGED, "value": 1, "entity_id": "tx_001"},
            {"metric": LeverageMetrics.TAGGED, "value": 1, "entity_id": "tx_002"},
            {"metric": LeverageMetrics.MATCH_LATENCY_MS, "value": 45.2, "entity_id": "tx_003"},
        ]

        result = service.recordDataBatch(metrics)

        assert result == 3
        assert len(mock_queue_adapter.messages) == 3


class TestAirflowContextAutoDetect:
    """Tests for AirflowContext.from_airflow auto-detection."""

    def test_from_airflow_without_airflow_installed(self) -> None:
        """Test that from_airflow raises RuntimeError when Airflow not installed."""
        with pytest.raises(RuntimeError) as exc_info:
            AirflowContext.from_airflow()

        assert "Airflow" in str(exc_info.value)
