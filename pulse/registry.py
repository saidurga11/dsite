"""Python-based metrics registry for the Pulse SDK."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from pulse.constants import MetricType


class PulseQueues(str, Enum):
    """Available Pulse queues."""

    LEVERAGE_METRICS = "PULSE_LEVERAGE_METRICS_QUEUE"
    # Add more queues as needed


class Owners(str, Enum):
    """Service owners."""

    DATA_SCIENCE = "data_science"
    MLE = "mle"
    DATA_ENGINEERING = "data_engineering"
    # Add more owners as needed


@dataclass(frozen=True)
class Metric:
    """Definition of a single metric."""

    name: str
    type: MetricType = MetricType.COUNTER
    deduplicate: bool = True
    description: str = ""


@dataclass(frozen=True)
class ServiceSchema:
    """Schema for a service registration."""

    service: str
    queue_name: PulseQueues
    owner: Owners
    metrics: tuple[Metric, ...] = field(default_factory=tuple)

    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name."""
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None

    def has_metric(self, name: str) -> bool:
        """Check if a metric is registered."""
        return self.get_metric(name) is not None


# =============================================================================
# METRICS REGISTRY - Add your service registrations here
# =============================================================================

METRICS_REGISTRY: list[ServiceSchema] = [
    ServiceSchema(
        service="leverage",
        queue_name=PulseQueues.LEVERAGE_METRICS,
        owner=Owners.DATA_SCIENCE,
        metrics=(
            Metric(
                name="tagged",
                type=MetricType.COUNTER,
                deduplicate=True,
                description="Transactions processed by tagging",
            ),
            Metric(
                name="match_latency_ms",
                type=MetricType.TIMING,
                deduplicate=False,
                description="Match latency in milliseconds",
            ),
        ),
    ),
    # Add more services here...
]


def get_service_registry(service: str) -> Optional[ServiceSchema]:
    """
    Get a service registration by name.

    Args:
        service: The service name to look up

    Returns:
        The ServiceSchema if found, None otherwise
    """
    for schema in METRICS_REGISTRY:
        if schema.service == service:
            return schema
    return None


def list_services() -> list[str]:
    """List all registered service names."""
    return [schema.service for schema in METRICS_REGISTRY]
