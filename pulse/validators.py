"""Validators for the Pulse SDK."""

import math
from typing import Any, Optional

from pulse.constants import (
    MAX_ENTITY_ID_LENGTH,
    MAX_METRIC_NAME_LENGTH,
    MAX_TAG_KEY_LENGTH,
    MAX_TAG_VALUE_LENGTH,
    MAX_TAGS_PER_METRIC,
    METRIC_NAME_PATTERN,
)
from pulse.exceptions import ValidationError
from pulse.models import MetricDefinition


class MetricValidator:
    """Validates metric names against registration."""

    def __init__(self, registered_metrics: dict[str, MetricDefinition]) -> None:
        """
        Initialize with registered metrics.

        Args:
            registered_metrics: Dictionary of metric name to MetricDefinition
        """
        self._registered_metrics = registered_metrics

    def validate(self, metric_name: str) -> MetricDefinition:
        """
        Validate a metric name and return its definition.

        Args:
            metric_name: The metric name to validate

        Returns:
            The MetricDefinition for the metric

        Raises:
            ValidationError: If the metric name is invalid or unregistered
        """
        if not metric_name:
            raise ValidationError("Metric name cannot be empty")

        if not isinstance(metric_name, str):
            raise ValidationError(
                f"Metric name must be a string, got {type(metric_name).__name__}"
            )

        if len(metric_name) > MAX_METRIC_NAME_LENGTH:
            raise ValidationError(
                f"Metric name exceeds maximum length of {MAX_METRIC_NAME_LENGTH}"
            )

        if not METRIC_NAME_PATTERN.match(metric_name):
            raise ValidationError(
                f"Metric name '{metric_name}' contains invalid characters. "
                "Must start with a letter and contain only letters, numbers, "
                "underscores, dots, or hyphens."
            )

        if metric_name not in self._registered_metrics:
            raise ValidationError(f"Metric '{metric_name}' is not registered")

        return self._registered_metrics[metric_name]


class ValueValidator:
    """Validates metric values."""

    @staticmethod
    def validate(value: Any) -> float:
        """
        Validate and convert a metric value.

        Args:
            value: The value to validate

        Returns:
            The value as a float

        Raises:
            ValidationError: If the value is invalid
        """
        if value is None:
            raise ValidationError("Value cannot be None")

        if not isinstance(value, (int, float)):
            raise ValidationError(
                f"Value must be numeric, got {type(value).__name__}"
            )

        # Convert to float
        float_value = float(value)

        if math.isnan(float_value):
            raise ValidationError("Value cannot be NaN")

        if math.isinf(float_value):
            raise ValidationError("Value cannot be infinite")

        return float_value


class TagValidator:
    """Validates and normalizes tags."""

    @staticmethod
    def validate(tags: Any) -> dict[str, str]:
        """
        Validate and normalize tags.

        Args:
            tags: The tags to validate (can be None)

        Returns:
            Normalized tags dictionary with string values

        Raises:
            ValidationError: If tags are invalid
        """
        if tags is None:
            return {}

        if not isinstance(tags, dict):
            raise ValidationError(
                f"Tags must be a dictionary, got {type(tags).__name__}"
            )

        if len(tags) > MAX_TAGS_PER_METRIC:
            raise ValidationError(
                f"Too many tags: {len(tags)} exceeds maximum of {MAX_TAGS_PER_METRIC}"
            )

        normalized: dict[str, str] = {}

        for key, value in tags.items():
            # Validate key
            if not isinstance(key, str):
                raise ValidationError(
                    f"Tag key must be a string, got {type(key).__name__}"
                )

            if not key.strip():
                raise ValidationError("Tag key cannot be empty or whitespace")

            if len(key) > MAX_TAG_KEY_LENGTH:
                raise ValidationError(
                    f"Tag key '{key}' exceeds maximum length of {MAX_TAG_KEY_LENGTH}"
                )

            # Convert value to string and validate length
            str_value = str(value) if value is not None else ""

            if len(str_value) > MAX_TAG_VALUE_LENGTH:
                raise ValidationError(
                    f"Tag value for key '{key}' exceeds maximum length of "
                    f"{MAX_TAG_VALUE_LENGTH}"
                )

            normalized[key] = str_value

        return normalized


class EntityIdValidator:
    """Validates entity IDs."""

    @staticmethod
    def validate(entity_id: Any, metric_def: MetricDefinition) -> str:
        """
        Validate an entity ID.

        Args:
            entity_id: The entity ID to validate
            metric_def: The metric definition (for dedup check)

        Returns:
            The validated entity ID as a string

        Raises:
            ValidationError: If entity ID is invalid
        """
        # For non-dedup metrics, entity_id can be empty/None
        if not metric_def.deduplicate:
            if entity_id is None:
                return ""
            return str(entity_id)

        # For dedup metrics, entity_id is required
        if entity_id is None:
            raise ValidationError(
                f"entity_id is required for metric '{metric_def.name}' "
                "(deduplication is enabled)"
            )

        if not isinstance(entity_id, str):
            entity_id = str(entity_id)

        if not entity_id.strip():
            raise ValidationError(
                f"entity_id cannot be empty for metric '{metric_def.name}' "
                "(deduplication is enabled)"
            )

        if len(entity_id) > MAX_ENTITY_ID_LENGTH:
            raise ValidationError(
                f"entity_id exceeds maximum length of {MAX_ENTITY_ID_LENGTH}"
            )

        return entity_id
