"""PulseClient for emitting metrics to a Redis queue."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional, Union

from pulse.exceptions import ConfigurationError, ValidationError
from pulse.idempotency import IdempotencyKeyBuilder
from pulse.models import AirflowContext, MetricMessage, ServiceRegistration
from pulse.queue_adapter import EQMAdapter, QueueAdapter
from pulse.registration import RegistrationLoader
from pulse.validators import (
    EntityIdValidator,
    MetricValidator,
    ValueValidator,
)

logger = logging.getLogger(__name__)


class PulseClient:
    """
    Client for emitting operational metrics to a Redis queue.

    Usage:
        from pulse import PulseClient, AirflowContext

        context = AirflowContext(
            dag_id="my_dag",
            task_id="my_task",
            run_id="scheduled__2026-01-08T14:00:00",
        )

        pulse = PulseClient(service="leverage", airflow_context=context)

        pulse.emit(
            metric_name="tagged",
            value=1,
            entity_id="tx_abc123",
        )
    """

    def __init__(
        self,
        service: str,
        airflow_context: AirflowContext,
        queue_adapter: Optional[QueueAdapter] = None,
    ) -> None:
        """
        Initialize client for a registered service.

        Args:
            service: Registered service name (e.g., "leverage")
            airflow_context: Airflow dag_id, task_id, run_id for dedup
            queue_adapter: Optional adapter for testing (uses EQM by default)

        Raises:
            ConfigurationError: If service not registered or config invalid
        """
        # Validate airflow_context
        self._validate_airflow_context(airflow_context)
        self._airflow_context = airflow_context

        # Load service registration
        loader = RegistrationLoader()
        self._registration: ServiceRegistration = loader.load(service)

        # Initialize components
        self._metric_validator = MetricValidator(self._registration.metrics)
        self._idempotency_builder = IdempotencyKeyBuilder(airflow_context)

        # Use provided adapter or create EQM adapter
        if queue_adapter is not None:
            self._queue_adapter = queue_adapter
        else:
            self._queue_adapter = EQMAdapter(self._registration.queue_name)

    def _validate_airflow_context(self, context: Any) -> None:
        """
        Validate the Airflow context.

        Args:
            context: The context to validate

        Raises:
            ConfigurationError: If context is invalid
        """
        if context is None:
            raise ConfigurationError("airflow_context cannot be None")

        if not isinstance(context, AirflowContext):
            raise ConfigurationError(
                f"airflow_context must be an AirflowContext instance, "
                f"got {type(context).__name__}"
            )

        if not context.dag_id or not context.dag_id.strip():
            raise ConfigurationError("airflow_context.dag_id cannot be empty")

        if not context.task_id or not context.task_id.strip():
            raise ConfigurationError("airflow_context.task_id cannot be empty")

        if not context.run_id or not context.run_id.strip():
            raise ConfigurationError("airflow_context.run_id cannot be empty")

    def emit(
        self,
        metric_name: str,
        value: Union[int, float],
        entity_id: str,
    ) -> bool:
        """
        Emit a single metric.

        Args:
            metric_name: Registered metric name
            value: Numeric value
            entity_id: Unique entity identifier (e.g., transaction_id)

        Returns:
            True if sent, False if rejected (duplicate or infra error)

        Raises:
            ValidationError: If parameters invalid (fail fast)
        """
        # Validate all parameters
        metric_def = self._metric_validator.validate(metric_name)
        validated_value = ValueValidator.validate(value)
        validated_entity_id = EntityIdValidator.validate(entity_id, metric_def)

        # Build idempotency key
        idempotency_key = self._idempotency_builder.build(
            metric_name=metric_name,
            entity_id=validated_entity_id,
            metric_def=metric_def,
        )

        # Create timestamp
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build message
        message = MetricMessage(
            timestamp=timestamp,
            metric_name=metric_name,
            value=validated_value,
            entity_id=validated_entity_id,
            idempotency_key=idempotency_key,
        )

        # Enqueue - infrastructure errors are caught and logged
        try:
            return self._queue_adapter.enqueue(message)
        except Exception as e:
            logger.error(f"Failed to emit metric '{metric_name}': {e}")
            return False

    def emit_batch(self, metrics: list[dict[str, Any]]) -> int:
        """
        Emit multiple metrics.

        Each dict must have: metric_name, value, entity_id

        Returns:
            Number of metrics successfully sent

        Raises:
            ValidationError: If any metric parameters invalid
        """
        if not isinstance(metrics, list):
            raise ValidationError(
                f"metrics must be a list, got {type(metrics).__name__}"
            )

        messages: list[MetricMessage] = []

        for i, metric in enumerate(metrics):
            if not isinstance(metric, dict):
                raise ValidationError(
                    f"Metric at index {i} must be a dict, "
                    f"got {type(metric).__name__}"
                )

            # Extract and validate fields
            try:
                metric_name = metric.get("metric_name")
                if metric_name is None:
                    raise ValidationError("metric_name is required")

                value = metric.get("value")
                if value is None:
                    raise ValidationError("value is required")

                entity_id = metric.get("entity_id")

                # Validate all parameters
                metric_def = self._metric_validator.validate(metric_name)
                validated_value = ValueValidator.validate(value)
                validated_entity_id = EntityIdValidator.validate(
                    entity_id, metric_def
                )

                # Build idempotency key
                idempotency_key = self._idempotency_builder.build(
                    metric_name=metric_name,
                    entity_id=validated_entity_id,
                    metric_def=metric_def,
                )

                # Create timestamp
                timestamp = datetime.now(timezone.utc).isoformat()

                # Build message
                message = MetricMessage(
                    timestamp=timestamp,
                    metric_name=metric_name,
                    value=validated_value,
                    entity_id=validated_entity_id,
                    idempotency_key=idempotency_key,
                )
                messages.append(message)

            except ValidationError as e:
                raise ValidationError(f"Metric at index {i}: {e}")

        # Enqueue all messages
        try:
            return self._queue_adapter.enqueue_batch(messages)
        except Exception as e:
            logger.error(f"Failed to emit batch: {e}")
            return 0
