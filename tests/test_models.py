"""Tests for Pulse SDK data models."""

import pytest

from pulse import AirflowContext
from pulse.models import MetricMessage


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
        hash(context)  # Should not raise


class TestMetricMessage:
    """Tests for MetricMessage dataclass."""

    def test_create_metric_message(self) -> None:
        """Test creating a metric message."""
        message = MetricMessage(
            timestamp="2026-01-08T14:30:00.123456Z",
            metric_name="tagged",
            value=1.0,
            idempotency_key="dag_task_run_tagged",
        )

        assert message.timestamp == "2026-01-08T14:30:00.123456Z"
        assert message.metric_name == "tagged"
        assert message.value == 1.0
        assert message.idempotency_key == "dag_task_run_tagged"

    def test_message_to_dict(self) -> None:
        """Test converting message to dictionary."""
        message = MetricMessage(
            timestamp="2026-01-08T14:30:00Z",
            metric_name="tagged",
            value=1.0,
            idempotency_key="test_key",
        )

        result = message.to_dict()

        assert result == {
            "timestamp": "2026-01-08T14:30:00Z",
            "metric_name": "tagged",
            "value": 1.0,
            "idempotency_key": "test_key",
        }

    def test_message_is_frozen(self) -> None:
        """Test that MetricMessage is immutable."""
        message = MetricMessage(
            timestamp="2026-01-08T14:30:00Z",
            metric_name="test",
            value=1.0,
            idempotency_key="key",
        )

        with pytest.raises(AttributeError):
            message.value = 2.0  # type: ignore
