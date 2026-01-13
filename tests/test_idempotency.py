"""Tests for Pulse SDK idempotency module."""

import re
import pytest

from pulse.constants import MetricType
from pulse.idempotency import IdempotencyKeyBuilder, TagsHasher
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


class TestTagsHasher:
    """Tests for TagsHasher."""

    def test_hash_empty_dict(self) -> None:
        """Test hashing empty dictionary."""
        result = TagsHasher.hash({})

        assert len(result) == 16
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_deterministic(self) -> None:
        """Test that same tags produce same hash."""
        tags = {"category": "mca", "caller": "de"}

        hash1 = TagsHasher.hash(tags)
        hash2 = TagsHasher.hash(tags)

        assert hash1 == hash2

    def test_hash_order_independent(self) -> None:
        """Test that tag order doesn't affect hash."""
        tags1 = {"a": "1", "b": "2", "c": "3"}
        tags2 = {"c": "3", "a": "1", "b": "2"}
        tags3 = {"b": "2", "c": "3", "a": "1"}

        hash1 = TagsHasher.hash(tags1)
        hash2 = TagsHasher.hash(tags2)
        hash3 = TagsHasher.hash(tags3)

        assert hash1 == hash2 == hash3

    def test_hash_case_insensitive_keys(self) -> None:
        """Test that key case doesn't affect hash."""
        tags1 = {"Key": "value", "ANOTHER": "val"}
        tags2 = {"key": "value", "another": "val"}
        tags3 = {"KEY": "value", "Another": "val"}

        hash1 = TagsHasher.hash(tags1)
        hash2 = TagsHasher.hash(tags2)
        hash3 = TagsHasher.hash(tags3)

        assert hash1 == hash2 == hash3

    def test_hash_whitespace_normalized(self) -> None:
        """Test that whitespace is normalized."""
        tags1 = {"  key  ": "  value  "}
        tags2 = {"key": "value"}

        hash1 = TagsHasher.hash(tags1)
        hash2 = TagsHasher.hash(tags2)

        assert hash1 == hash2

    def test_hash_different_values_produce_different_hashes(self) -> None:
        """Test that different values produce different hashes."""
        tags1 = {"category": "mca"}
        tags2 = {"category": "factor"}

        hash1 = TagsHasher.hash(tags1)
        hash2 = TagsHasher.hash(tags2)

        assert hash1 != hash2

    def test_hash_different_keys_produce_different_hashes(self) -> None:
        """Test that different keys produce different hashes."""
        tags1 = {"category": "value"}
        tags2 = {"caller": "value"}

        hash1 = TagsHasher.hash(tags1)
        hash2 = TagsHasher.hash(tags2)

        assert hash1 != hash2

    def test_hash_returns_16_chars(self) -> None:
        """Test that hash is always 16 characters."""
        test_cases = [
            {},
            {"a": "b"},
            {"key": "value", "key2": "value2"},
            {f"key_{i}": f"value_{i}" for i in range(10)},
        ]

        for tags in test_cases:
            result = TagsHasher.hash(tags)
            assert len(result) == 16

    def test_hash_with_none_value(self) -> None:
        """Test hashing tags with None value."""
        tags = {"key": None}

        result = TagsHasher.hash(tags)

        assert len(result) == 16

    def test_hash_with_numeric_values(self) -> None:
        """Test hashing tags with numeric values (converted to strings)."""
        tags1 = {"count": 42}
        tags2 = {"count": "42"}

        hash1 = TagsHasher.hash(tags1)
        hash2 = TagsHasher.hash(tags2)

        assert hash1 == hash2
