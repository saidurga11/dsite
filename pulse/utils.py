"""Utility functions for the Pulse SDK."""

import math
from typing import Any

from pulse.exceptions import ValidationError
from pulse.models import AirflowContext
from pulse.registry import MAX_ENTITY_ID_LENGTH, Metric, ServiceSchema


def validate_metric(metric: Metric, service: ServiceSchema) -> None:
    """
    Validate that a metric is registered for the service.

    Raises:
        ValidationError: If the metric is invalid or not registered
    """
    if metric is None:
        raise ValidationError("metric is required")

    if not isinstance(metric, Metric):
        raise ValidationError(f"metric must be a Metric object, got {type(metric).__name__}")

    if not service.has_metric(metric):
        raise ValidationError(
            f"Metric '{metric.name}' is not registered for service '{service.service}'"
        )


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


def validate_entity_id(entity_id: Any) -> str:
    """
    Validate an entity ID.

    Raises:
        ValidationError: If entity ID is invalid
    """
    if entity_id is None:
        raise ValidationError("entity_id is required")

    if not isinstance(entity_id, str):
        entity_id = str(entity_id)

    if not entity_id.strip():
        raise ValidationError("entity_id cannot be empty")

    if len(entity_id) > MAX_ENTITY_ID_LENGTH:
        raise ValidationError(f"entity_id exceeds maximum length of {MAX_ENTITY_ID_LENGTH}")

    return entity_id


def build_idempotency_key(
    context: AirflowContext,
    metric_name: str,
    entity_id: str,
) -> str:
    """
    Build an idempotency key for a metric.

    Returns: {dag_id}_{task_id}_{run_id}_{metric_name}_{entity_id}
    """
    return f"{context.dag_id}_{context.task_id}_{context.run_id}_{metric_name}_{entity_id}"
