"""Tests for Pulse SDK idempotency module."""

import re
import pytest

from pulse import AirflowContext, Metric, MetricType
from pulse.idempotency import build_idempotency_key


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

    @pytest.fixture
    def dedup_metric(self) -> Metric:
        """Metric with deduplication enabled."""
        return Metric(name="tagged", type=MetricType.COUNTER, deduplicate=True)

    @pytest.fixture
    def no_dedup_metric(self) -> Metric:
        """Metric with deduplication disabled."""
        return Metric(name="latency_ms", type=MetricType.TIMING, deduplicate=False)

    def test_build_deterministic_key_with_dedup(
        self, context: AirflowContext, dedup_metric: Metric
    ) -> None:
        """Test that dedup-enabled metrics produce deterministic keys."""
        key = build_idempotency_key(context, "tagged", "tx_abc123", dedup_metric)

        expected = (
            "leverage_tagging_dag_"
            "tag_transactions_"
            "scheduled__2026-01-08T14:00:00_"
            "tagged_"
            "tx_abc123"
        )
        assert key == expected

    def test_build_same_inputs_produce_same_key(
        self, context: AirflowContext, dedup_metric: Metric
    ) -> None:
        """Test that same inputs always produce the same key."""
        key1 = build_idempotency_key(context, "tagged", "tx_123", dedup_metric)
        key2 = build_idempotency_key(context, "tagged", "tx_123", dedup_metric)
        assert key1 == key2

    def test_build_different_entity_ids_produce_different_keys(
        self, context: AirflowContext, dedup_metric: Metric
    ) -> None:
        """Test that different entity_ids produce different keys."""
        key1 = build_idempotency_key(context, "tagged", "tx_123", dedup_metric)
        key2 = build_idempotency_key(context, "tagged", "tx_456", dedup_metric)
        assert key1 != key2

    def test_build_uuid_for_non_dedup_metrics(
        self, context: AirflowContext, no_dedup_metric: Metric
    ) -> None:
        """Test that non-dedup metrics produce UUID keys."""
        key = build_idempotency_key(context, "latency_ms", "tx_123", no_dedup_metric)

        # UUID format: 8-4-4-4-12 hex characters
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        assert uuid_pattern.match(key)

    def test_build_non_dedup_produces_unique_keys(
        self, context: AirflowContext, no_dedup_metric: Metric
    ) -> None:
        """Test that non-dedup metrics produce unique keys each call."""
        key1 = build_idempotency_key(context, "latency_ms", "tx_123", no_dedup_metric)
        key2 = build_idempotency_key(context, "latency_ms", "tx_123", no_dedup_metric)
        assert key1 != key2

    def test_build_with_different_contexts(self) -> None:
        """Test that different contexts produce different keys."""
        context1 = AirflowContext("dag1", "task1", "run1")
        context2 = AirflowContext("dag2", "task2", "run2")
        metric = Metric(name="test", deduplicate=True)

        key1 = build_idempotency_key(context1, "test", "entity", metric)
        key2 = build_idempotency_key(context2, "test", "entity", metric)
        assert key1 != key2
