"""Idempotency key generation for the Pulse SDK."""

import uuid

from pulse.models import AirflowContext
from pulse.registry import Metric


def build_idempotency_key(
    context: AirflowContext,
    metric_name: str,
    entity_id: str,
    metric: Metric,
) -> str:
    """
    Build an idempotency key for a metric.

    For metrics with deduplicate=True, builds a deterministic key:
        {dag_id}_{task_id}_{run_id}_{metric_name}_{entity_id}

    For metrics with deduplicate=False, generates a UUID.
    """
    if not metric.deduplicate:
        return str(uuid.uuid4())

    return f"{context.dag_id}_{context.task_id}_{context.run_id}_{metric_name}_{entity_id}"
