"""Data models for the Pulse SDK."""

from dataclasses import dataclass, field
from typing import Any

from pulse.constants import MetricType


@dataclass(frozen=True)
class AirflowContext:
    """
    Context from Airflow for idempotency key generation.

    Attributes:
        dag_id: The DAG identifier
        task_id: The task identifier within the DAG
        run_id: The run identifier (e.g., "scheduled__2026-01-08T14:00:00")
    """

    dag_id: str
    task_id: str
    run_id: str


@dataclass(frozen=True)
class MetricDefinition:
    """
    Definition of a registered metric.

    Attributes:
        name: Metric name
        metric_type: Type of metric (counter, gauge, timing)
        deduplicate: Whether to deduplicate based on idempotency key
        description: Human-readable description
    """

    name: str
    metric_type: MetricType
    deduplicate: bool
    description: str = ""


@dataclass(frozen=True)
class ServiceRegistration:
    """
    Service registration configuration.

    Attributes:
        service: Service name
        owner: Team or individual owning the service
        queue_name: Name of the Redis queue for this service
        metrics: Dictionary of metric name to MetricDefinition
    """

    service: str
    owner: str
    queue_name: str
    metrics: dict[str, MetricDefinition] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricMessage:
    """
    Message to be sent to the queue.

    Attributes:
        timestamp: ISO 8601 timestamp
        metric_name: Name of the metric
        value: Numeric value
        entity_id: Unique entity identifier
        idempotency_key: Key for deduplication
    """

    timestamp: str
    metric_name: str
    value: float
    entity_id: str
    idempotency_key: str

    def to_dict(self) -> dict[str, Any]:
        """Convert the message to a dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "metric_name": self.metric_name,
            "value": self.value,
            "entity_id": self.entity_id,
            "idempotency_key": self.idempotency_key,
        }
