"""Idempotency key builder and tags hasher for the Pulse SDK."""

import hashlib
import json
import uuid
from typing import Any

from pulse.models import AirflowContext, MetricDefinition


class IdempotencyKeyBuilder:
    """Builds idempotency keys for metric deduplication."""

    def __init__(self, airflow_context: AirflowContext) -> None:
        """
        Initialize with Airflow context.

        Args:
            airflow_context: The Airflow context containing dag_id, task_id, run_id
        """
        self._context = airflow_context

    def build(
        self,
        metric_name: str,
        entity_id: str,
        metric_def: MetricDefinition,
    ) -> str:
        """
        Build an idempotency key for a metric emit.

        For metrics with deduplicate=True, builds a deterministic key:
            {dag_id}_{task_id}_{run_id}_{metric_name}_{entity_id}

        For metrics with deduplicate=False, generates a UUID.

        Args:
            metric_name: The name of the metric
            entity_id: The entity identifier
            metric_def: The metric definition

        Returns:
            The idempotency key
        """
        if not metric_def.deduplicate:
            # Generate unique key for non-dedup metrics
            return str(uuid.uuid4())

        # Build deterministic key for dedup metrics
        return (
            f"{self._context.dag_id}_"
            f"{self._context.task_id}_"
            f"{self._context.run_id}_"
            f"{metric_name}_"
            f"{entity_id}"
        )


class TagsHasher:
    """Computes deterministic hashes of tags for database grouping."""

    @staticmethod
    def hash(tags: dict[str, Any]) -> str:
        """
        Compute a 16-character hex hash of tags.

        Properties:
        - Deterministic: same tags produce the same hash
        - Order-independent: {"a": "1", "b": "2"} == {"b": "2", "a": "1"}
        - Case-insensitive keys: {"Key": "v"} == {"key": "v"}
        - Whitespace normalized: {"  k  ": "  v  "} == {"k": "v"}

        Args:
            tags: Dictionary of tag key-value pairs

        Returns:
            16-character hex hash string
        """
        if not tags:
            # Hash of empty dict
            return hashlib.md5(b"{}").hexdigest()[:16]

        # Normalize tags: lowercase keys, strip whitespace
        normalized = {}
        for key, value in tags.items():
            normalized_key = str(key).lower().strip()
            normalized_value = str(value).strip() if value is not None else ""
            normalized[normalized_key] = normalized_value

        # Sort by keys for order-independence
        sorted_items = sorted(normalized.items())

        # Create deterministic JSON representation
        canonical = json.dumps(sorted_items, separators=(",", ":"), sort_keys=True)

        # Compute hash and return first 16 characters
        return hashlib.md5(canonical.encode("utf-8")).hexdigest()[:16]
