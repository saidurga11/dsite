"""Tests for Pulse SDK idempotency module."""

import pytest

from pulse import AirflowContext
from pulse.utils import build_idempotency_key


class TestBuildIdempotencyKey:
    """Tests for build_idempotency_key function."""

    @pytest.fixture
    def context(self) -> AirflowContext:
        """Create a sample Airflow context."""
        return AirflowContext(
            dag_id="leverage_tagging_dag",
            task_id="tag_transactions",
            run_id="scheduled__2026-01-08T14:00:00",
        )

    def test_build_deterministic_key(self, context: AirflowContext) -> None:
        """Test that build produces deterministic keys."""
        key = build_idempotency_key(context, "tagged")

        expected = (
            "leverage_tagging_dag_"
            "tag_transactions_"
            "scheduled__2026-01-08T14:00:00_"
            "tagged"
        )
        assert key == expected

    def test_build_same_inputs_produce_same_key(self, context: AirflowContext) -> None:
        """Test that same inputs always produce the same key."""
        key1 = build_idempotency_key(context, "tagged")
        key2 = build_idempotency_key(context, "tagged")
        assert key1 == key2

    def test_build_different_metrics_produce_different_keys(self, context: AirflowContext) -> None:
        """Test that different metrics produce different keys."""
        key1 = build_idempotency_key(context, "tagged")
        key2 = build_idempotency_key(context, "latency_ms")
        assert key1 != key2

    def test_build_with_different_contexts(self) -> None:
        """Test that different contexts produce different keys."""
        context1 = AirflowContext("dag1", "task1", "run1")
        context2 = AirflowContext("dag2", "task2", "run2")

        key1 = build_idempotency_key(context1, "test")
        key2 = build_idempotency_key(context2, "test")
        assert key1 != key2
