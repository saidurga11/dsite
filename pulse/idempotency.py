"""Idempotency key builder for the Pulse SDK."""

import uuid

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
