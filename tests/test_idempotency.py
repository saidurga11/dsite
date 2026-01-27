"""Tests for Pulse SDK idempotency module."""

import re

import pytest

from pulse.constants import MetricType
from pulse.idempotency import IdempotencyKeyBuilder
from pulse.models import AirflowContext, MetricDefinition


class TestIdempotencyKeyBuilder:
    """Tests for IdempotencyKeyBuilder."""

    @pytest.fixture
    def airflow_context(self) -> AirflowContext:
        """Create a sample Airflow context."""
        return AirflowContext(
            dag_id="leverage_tagging_dag",
            task_id="tag_transactions",
            run_id="scheduled__2026-01-08T14:00:00",
        )

    @pytest.fixture
    def builder(self, airflow_context: AirflowContext) -> IdempotencyKeyBuilder:
        """Create an IdempotencyKeyBuilder."""
        return IdempotencyKeyBuilder(airflow_context)

    @pytest.fixture
    def dedup_metric(self) -> MetricDefinition:
        """Create a metric with deduplication enabled."""
        return MetricDefinition(
            name="tagged",
            metric_type=MetricType.COUNTER,
            deduplicate=True,
        )

    @pytest.fixture
    def non_dedup_metric(self) -> MetricDefinition:
        """Create a metric with deduplication disabled."""
        return MetricDefinition(
            name="latency_ms",
            metric_type=MetricType.TIMING,
            deduplicate=False,
        )

    def test_build_deterministic_key_with_dedup(
        self,
        builder: IdempotencyKeyBuilder,
        dedup_metric: MetricDefinition,
    ) -> None:
        """Test that dedup-enabled metrics produce deterministic keys."""
        key = builder.build(
            metric_name="tagged",
            entity_id="tx_abc123",
            metric_def=dedup_metric,
        )

        expected = (
            "leverage_tagging_dag_"
            "tag_transactions_"
            "scheduled__2026-01-08T14:00:00_"
            "tagged_"
            "tx_abc123"
        )
        assert key == expected

    def test_build_same_inputs_produce_same_key(
        self,
        builder: IdempotencyKeyBuilder,
        dedup_metric: MetricDefinition,
    ) -> None:
        """Test that same inputs always produce the same key."""
        key1 = builder.build("tagged", "tx_123", dedup_metric)
        key2 = builder.build("tagged", "tx_123", dedup_metric)

        assert key1 == key2

    def test_build_different_entity_ids_produce_different_keys(
        self,
        builder: IdempotencyKeyBuilder,
        dedup_metric: MetricDefinition,
    ) -> None:
        """Test that different entity_ids produce different keys."""
        key1 = builder.build("tagged", "tx_123", dedup_metric)
        key2 = builder.build("tagged", "tx_456", dedup_metric)

        assert key1 != key2

    def test_build_uuid_for_non_dedup_metrics(
        self,
        builder: IdempotencyKeyBuilder,
        non_dedup_metric: MetricDefinition,
    ) -> None:
        """Test that non-dedup metrics produce UUID keys."""
        key = builder.build("latency_ms", "tx_123", non_dedup_metric)

        # UUID format: 8-4-4-4-12 hex characters
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        assert uuid_pattern.match(key)

    def test_build_non_dedup_produces_unique_keys(
        self,
        builder: IdempotencyKeyBuilder,
        non_dedup_metric: MetricDefinition,
    ) -> None:
        """Test that non-dedup metrics produce unique keys each call."""
        key1 = builder.build("latency_ms", "tx_123", non_dedup_metric)
        key2 = builder.build("latency_ms", "tx_123", non_dedup_metric)

        # Keys should be different (UUIDs)
        assert key1 != key2

    def test_build_with_different_contexts(self) -> None:
        """Test that different contexts produce different keys."""
        context1 = AirflowContext("dag1", "task1", "run1")
        context2 = AirflowContext("dag2", "task2", "run2")

        builder1 = IdempotencyKeyBuilder(context1)
        builder2 = IdempotencyKeyBuilder(context2)

        dedup_metric = MetricDefinition(
            name="test",
            metric_type=MetricType.COUNTER,
            deduplicate=True,
        )

        key1 = builder1.build("test", "entity", dedup_metric)
        key2 = builder2.build("test", "entity", dedup_metric)

        assert key1 != key2
