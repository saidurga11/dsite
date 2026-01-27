"""AggregationMonitoringService for recording metrics to a Redis queue."""

import logging
from datetime import datetime, timezone
from typing import Any, Optional, Union

from pulse.exceptions import ConfigurationError, ValidationError
from pulse.models import AirflowContext, MetricMessage
from pulse.queue_adapter import EQMAdapter, QueueAdapter
from pulse.registry import ServiceSchema, get_service_registry, list_services
from pulse.utils import build_idempotency_key, validate_entity_id, validate_metric, validate_value

logger = logging.getLogger(__name__)


class AggregationMonitoringService:
    """
    Service for recording operational metrics to a Redis queue.

    The Airflow context is automatically detected when running inside an Airflow task.

    Usage in Airflow:
        from pulse import AggregationMonitoringService

        monitor = AggregationMonitoringService(service="leverage")
        monitor.recordData(metric_name="tagged", value=1, entity_id="tx_abc123")

    Usage in tests:
        from pulse import AggregationMonitoringService, AirflowContext, MockQueueAdapter

        context = AirflowContext(dag_id="test", task_id="test", run_id="test")
        monitor = AggregationMonitoringService(
            service="leverage",
            airflow_context=context,
            queue_adapter=MockQueueAdapter(),
        )
    """

    def __init__(
        self,
        service: str,
        airflow_context: Optional[AirflowContext] = None,
        queue_adapter: Optional[QueueAdapter] = None,
    ) -> None:
        """
        Initialize service for a registered service.

        Args:
            service: Registered service name (e.g., "leverage")
            airflow_context: Optional - auto-detected from Airflow if not provided
            queue_adapter: Optional adapter for testing (uses EQM by default)
        """
        # Get airflow context
        if airflow_context is None:
            self._context = AirflowContext.from_airflow()
        else:
            self._validate_context(airflow_context)
            self._context = airflow_context

        # Load service
        self._service = self._load_service(service)

        # Setup queue adapter
        self._queue = queue_adapter or EQMAdapter(self._service.queue_name.value)

    def _validate_context(self, context: Any) -> None:
        """Validate a manually provided Airflow context."""
        if not isinstance(context, AirflowContext):
            raise ConfigurationError(
                f"airflow_context must be an AirflowContext instance, got {type(context).__name__}"
            )
        if not context.dag_id or not context.dag_id.strip():
            raise ConfigurationError("airflow_context.dag_id cannot be empty")
        if not context.task_id or not context.task_id.strip():
            raise ConfigurationError("airflow_context.task_id cannot be empty")
        if not context.run_id or not context.run_id.strip():
            raise ConfigurationError("airflow_context.run_id cannot be empty")

    def _load_service(self, service: str) -> ServiceSchema:
        """Load and validate service registration."""
        if not service:
            raise ConfigurationError("Service name cannot be empty")

        schema = get_service_registry(service)
        if schema is None:
            raise ConfigurationError(
                f"Service '{service}' is not registered. Available: {list_services()}"
            )
        return schema

    def recordData(
        self,
        metric_name: str,
        value: Union[int, float],
        entity_id: str,
    ) -> bool:
        """
        Record a single metric.

        Returns:
            True if sent, False if rejected (duplicate or error)
        """
        # Validate
        metric = validate_metric(metric_name, self._service)
        validated_value = validate_value(value)
        validated_entity_id = validate_entity_id(entity_id, metric)

        # Build message
        message = MetricMessage(
            timestamp=datetime.now(timezone.utc).isoformat(),
            metric_name=metric_name,
            value=validated_value,
            entity_id=validated_entity_id,
            idempotency_key=build_idempotency_key(
                self._context, metric_name, validated_entity_id, metric
            ),
        )

        try:
            return self._queue.enqueue(message)
        except Exception as e:
            logger.error(f"Failed to record metric '{metric_name}': {e}")
            return False

    def recordDataBatch(self, metrics: list[dict[str, Any]]) -> int:
        """
        Record multiple metrics.

        Each dict must have: metric_name, value, entity_id

        Returns:
            Number of metrics successfully sent
        """
        if not isinstance(metrics, list):
            raise ValidationError(f"metrics must be a list, got {type(metrics).__name__}")

        messages: list[MetricMessage] = []

        for i, m in enumerate(metrics):
            if not isinstance(m, dict):
                raise ValidationError(f"Metric at index {i} must be a dict, got {type(m).__name__}")

            try:
                metric_name = m.get("metric_name")
                if metric_name is None:
                    raise ValidationError("metric_name is required")

                value = m.get("value")
                if value is None:
                    raise ValidationError("value is required")

                entity_id = m.get("entity_id")

                # Validate
                metric = validate_metric(metric_name, self._service)
                validated_value = validate_value(value)
                validated_entity_id = validate_entity_id(entity_id, metric)

                messages.append(MetricMessage(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    metric_name=metric_name,
                    value=validated_value,
                    entity_id=validated_entity_id,
                    idempotency_key=build_idempotency_key(
                        self._context, metric_name, validated_entity_id, metric
                    ),
                ))
            except ValidationError as e:
                raise ValidationError(f"Metric at index {i}: {e}")

        try:
            return self._queue.enqueue_batch(messages)
        except Exception as e:
            logger.error(f"Failed to record batch: {e}")
            return 0
