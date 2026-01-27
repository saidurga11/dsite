"""Utility functions for the Pulse SDK."""

import math
import uuid
from typing import Any

from pulse.exceptions import ValidationError
from pulse.models import AirflowContext
from pulse.registry import MAX_ENTITY_ID_LENGTH, MAX_METRIC_NAME_LENGTH, METRIC_NAME_PATTERN, Metric, ServiceSchema


def validate_metric(metric_name: str, service: ServiceSchema) -> Metric:
    """
    Validate a metric name and return its definition.

    Raises:
        ValidationError: If the metric name is invalid or unregistered
    """
    if not metric_name:
        raise ValidationError("Metric name cannot be empty")

    if not isinstance(metric_name, str):
        raise ValidationError(f"Metric name must be a string, got {type(metric_name).__name__}")

    if len(metric_name) > MAX_METRIC_NAME_LENGTH:
        raise ValidationError(f"Metric name exceeds maximum length of {MAX_METRIC_NAME_LENGTH}")

    if not METRIC_NAME_PATTERN.match(metric_name):
        raise ValidationError(
            f"Metric name '{metric_name}' contains invalid characters. "
            "Must start with a letter and contain only letters, numbers, underscores, dots, or hyphens."
        )

    metric = service.get_metric(metric_name)
    if metric is None:
        raise ValidationError(f"Metric '{metric_name}' is not registered")

    return metric


def validate_value(value: Any) -> float:
    """
    Validate and convert a metric value.

    Raises:
        ValidationError: If the value is invalid
    """
    if value is None:
        raise ValidationError("Value cannot be None")

    if not isinstance(value, (int, float)):
        raise ValidationError(f"Value must be numeric, got {type(value).__name__}")

    float_value = float(value)

    if math.isnan(float_value):
        raise ValidationError("Value cannot be NaN")

    if math.isinf(float_value):
        raise ValidationError("Value cannot be infinite")

    return float_value


def validate_entity_id(entity_id: Any, metric: Metric) -> str:
    """
    Validate an entity ID.

    Raises:
        ValidationError: If entity ID is invalid
    """
    # For non-dedup metrics, entity_id can be empty/None
    if not metric.deduplicate:
        if entity_id is None:
            return ""
        return str(entity_id)

    # For dedup metrics, entity_id is required
    if entity_id is None:
        raise ValidationError(
            f"entity_id is required for metric '{metric.name}' (deduplication is enabled)"
        )

    if not isinstance(entity_id, str):
        entity_id = str(entity_id)

    if not entity_id.strip():
        raise ValidationError(
            f"entity_id cannot be empty for metric '{metric.name}' (deduplication is enabled)"
        )

    if len(entity_id) > MAX_ENTITY_ID_LENGTH:
        raise ValidationError(f"entity_id exceeds maximum length of {MAX_ENTITY_ID_LENGTH}")

    return entity_id


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
