"""Tests for Pulse SDK data models."""

import pytest

from pulse.constants import MetricType
from pulse.models import (
    AirflowContext,
    MetricDefinition,
    MetricMessage,
    ServiceRegistration,
)


class TestAirflowContext:
    """Tests for AirflowContext dataclass."""

    def test_create_valid_context(self) -> None:
        """Test creating a valid AirflowContext."""
        context = AirflowContext(
            dag_id="my_dag",
            task_id="my_task",
            run_id="scheduled__2026-01-08T14:00:00",
        )

        assert context.dag_id == "my_dag"
        assert context.task_id == "my_task"
        assert context.run_id == "scheduled__2026-01-08T14:00:00"

    def test_context_is_frozen(self) -> None:
        """Test that AirflowContext is immutable."""
        context = AirflowContext(
            dag_id="my_dag",
            task_id="my_task",
            run_id="run_123",
        )

        with pytest.raises(AttributeError):
            context.dag_id = "new_dag"  # type: ignore

    def test_context_equality(self) -> None:
        """Test that identical contexts are equal."""
        context1 = AirflowContext("dag", "task", "run")
        context2 = AirflowContext("dag", "task", "run")

        assert context1 == context2

    def test_context_hashable(self) -> None:
        """Test that AirflowContext is hashable."""
        context = AirflowContext("dag", "task", "run")
        # Should not raise
        hash(context)


class TestMetricDefinition:
    """Tests for MetricDefinition dataclass."""

    def test_create_counter_metric(self) -> None:
        """Test creating a counter metric definition."""
        metric = MetricDefinition(
            name="transactions",
            metric_type=MetricType.COUNTER,
            deduplicate=True,
            description="Transaction count",
        )

        assert metric.name == "transactions"
        assert metric.metric_type == MetricType.COUNTER
        assert metric.deduplicate is True
        assert metric.description == "Transaction count"

    def test_create_timing_metric(self) -> None:
        """Test creating a timing metric definition."""
        metric = MetricDefinition(
            name="latency_ms",
            metric_type=MetricType.TIMING,
            deduplicate=False,
        )

        assert metric.name == "latency_ms"
        assert metric.metric_type == MetricType.TIMING
        assert metric.deduplicate is False
        assert metric.description == ""  # Default value

    def test_metric_is_frozen(self) -> None:
        """Test that MetricDefinition is immutable."""
        metric = MetricDefinition(
            name="test",
            metric_type=MetricType.GAUGE,
            deduplicate=True,
        )

        with pytest.raises(AttributeError):
            metric.name = "new_name"  # type: ignore


class TestServiceRegistration:
    """Tests for ServiceRegistration dataclass."""

    def test_create_service_registration(self) -> None:
        """Test creating a service registration."""
        metrics = {
            "counter": MetricDefinition(
                name="counter",
                metric_type=MetricType.COUNTER,
                deduplicate=True,
            )
        }

        registration = ServiceRegistration(
            service="my_service",
            owner="my_team",
            queue_name="MY_QUEUE",
            metrics=metrics,
        )

        assert registration.service == "my_service"
        assert registration.owner == "my_team"
        assert registration.queue_name == "MY_QUEUE"
        assert "counter" in registration.metrics

    def test_registration_with_empty_metrics(self) -> None:
        """Test creating registration with no metrics."""
        registration = ServiceRegistration(
            service="my_service",
            owner="my_team",
            queue_name="MY_QUEUE",
        )

        assert registration.metrics == {}


class TestMetricMessage:
    """Tests for MetricMessage dataclass."""

    def test_create_metric_message(self) -> None:
        """Test creating a metric message."""
        message = MetricMessage(
            timestamp="2026-01-08T14:30:00.123456Z",
            metric_name="tagged",
            value=1.0,
            tags={"category": "mca"},
            idempotency_key="dag_task_run_tagged_tx123",
            tags_hash="a1b2c3d4e5f67890",
        )

        assert message.timestamp == "2026-01-08T14:30:00.123456Z"
        assert message.metric_name == "tagged"
        assert message.value == 1.0
        assert message.tags == {"category": "mca"}
        assert message.idempotency_key == "dag_task_run_tagged_tx123"
        assert message.tags_hash == "a1b2c3d4e5f67890"

    def test_message_to_dict(self) -> None:
        """Test converting message to dictionary."""
        message = MetricMessage(
            timestamp="2026-01-08T14:30:00Z",
            metric_name="tagged",
            value=1.0,
            tags={"key": "value"},
            idempotency_key="test_key",
            tags_hash="abc123",
        )

        result = message.to_dict()

        assert result == {
            "timestamp": "2026-01-08T14:30:00Z",
            "metric_name": "tagged",
            "value": 1.0,
            "tags": {"key": "value"},
            "idempotency_key": "test_key",
            "tags_hash": "abc123",
        }

    def test_message_is_frozen(self) -> None:
        """Test that MetricMessage is immutable."""
        message = MetricMessage(
            timestamp="2026-01-08T14:30:00Z",
            metric_name="test",
            value=1.0,
            tags={},
            idempotency_key="key",
            tags_hash="hash",
        )

        with pytest.raises(AttributeError):
            message.value = 2.0  # type: ignore

    def test_message_to_dict_creates_copy_of_tags(self) -> None:
        """Test that to_dict creates a copy of tags."""
        original_tags = {"key": "value"}
        message = MetricMessage(
            timestamp="2026-01-08T14:30:00Z",
            metric_name="test",
            value=1.0,
            tags=original_tags,
            idempotency_key="key",
            tags_hash="hash",
        )

        result = message.to_dict()
        result["tags"]["new_key"] = "new_value"

        # Original message tags should not be affected
        assert "new_key" not in message.tags
