"""
Pulse SDK - Operational metrics for Airflow DAGs.

Usage in Airflow (context auto-detected):
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

from pulse.client import AggregationMonitoringService
from pulse.constants import MetricType
from pulse.exceptions import ConfigurationError, PulseError, ValidationError
from pulse.models import AirflowContext
from pulse.queue_adapter import MockQueueAdapter
from pulse.registry import (
    METRICS_REGISTRY,
    Metric,
    Owners,
    PulseQueues,
    ServiceSchema,
)

__all__ = [
    "AggregationMonitoringService",
    "AirflowContext",
    "MockQueueAdapter",
    "METRICS_REGISTRY",
    "ServiceSchema",
    "Metric",
    "MetricType",
    "PulseQueues",
    "Owners",
    "PulseError",
    "ConfigurationError",
    "ValidationError",
]

__version__ = "0.1.0"
