"""
Pulse SDK - Operational metrics for Airflow DAGs.

Usage in Airflow (context auto-detected):
    from pulse import AggregationMonitoringService
    from pulse.registry import LeverageMetrics

    monitor = AggregationMonitoringService(service="leverage")
    monitor.recordData(metric=LeverageMetrics.TAGGED, value=1, entity_id="tx_abc123")

Usage in tests:
    from pulse import AggregationMonitoringService, AirflowContext, MockQueueAdapter
    from pulse.registry import LeverageMetrics

    context = AirflowContext(dag_id="test", task_id="test", run_id="test")
    monitor = AggregationMonitoringService(
        service="leverage",
        airflow_context=context,
        queue_adapter=MockQueueAdapter(),
    )
    monitor.recordData(metric=LeverageMetrics.TAGGED, value=100, entity_id="test")
"""

from pulse.client import AggregationMonitoringService
from pulse.exceptions import ConfigurationError, PulseError, ValidationError
from pulse.models import AirflowContext
from pulse.queue_adapter import MockQueueAdapter
from pulse.registry import (
    LeverageMetrics,
    METRICS_REGISTRY,
    Metric,
    MetricType,
    Owners,
    PulseQueues,
    ServiceSchema,
)

__all__ = [
    "AggregationMonitoringService",
    "AirflowContext",
    "MockQueueAdapter",
    "LeverageMetrics",
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
