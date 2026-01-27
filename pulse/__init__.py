"""
Pulse SDK - Operational metrics for Airflow DAGs.

A Python SDK for recording operational metrics to a Redis queue,
designed for use in Airflow DAGs to track transaction counts,
processing times, and error rates.

Usage:
    from pulse import AggregationMonitoringService, AirflowContext

    context = AirflowContext(
        dag_id="leverage_tagging_dag",
        task_id="tag_transactions",
        run_id="scheduled__2026-01-08T14:00:00",
    )

    monitor = AggregationMonitoringService(service="leverage", airflow_context=context)

    monitor.recordData(
        metric_name="tagged",
        value=1,
        entity_id="tx_abc123",
    )
"""

from pulse.client import AggregationMonitoringService
from pulse.constants import MetricType
from pulse.exceptions import ConfigurationError, EmitError, PulseError, ValidationError
from pulse.models import AirflowContext
from pulse.queue_adapter import MockQueueAdapter, QueueAdapter
from pulse.registry import (
    METRICS_REGISTRY,
    Metric,
    Owners,
    PulseQueues,
    ServiceSchema,
    get_service_registry,
    list_services,
)

__all__ = [
    # Main service
    "AggregationMonitoringService",
    # Models
    "AirflowContext",
    # Registry
    "METRICS_REGISTRY",
    "ServiceSchema",
    "Metric",
    "MetricType",
    "PulseQueues",
    "Owners",
    "get_service_registry",
    "list_services",
    # Exceptions
    "PulseError",
    "ConfigurationError",
    "ValidationError",
    "EmitError",
    # Queue adapters (for testing)
    "QueueAdapter",
    "MockQueueAdapter",
]

__version__ = "0.1.0"
