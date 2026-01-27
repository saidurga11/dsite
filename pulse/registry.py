"""Metrics registry and constants for the Pulse SDK."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class MetricType(str, Enum):
    """Supported metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    TIMING = "timing"


# Validation limits
MAX_METRIC_NAME_LENGTH = 255
MAX_ENTITY_ID_LENGTH = 512

# Metric name must start with letter, then letters/numbers/underscores/dots/hyphens
METRIC_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.\-]*$")


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
            Metric(name="tagged", type=MetricType.COUNTER),
            Metric(name="match_latency_ms", type=MetricType.TIMING),
        ),
    ),
    # Add more services here...
]


def get_service_registry(service: str) -> Optional[ServiceSchema]:
    """Get a service registration by name."""
    for schema in METRICS_REGISTRY:
        if schema.service == service:
            return schema
    return None


def list_services() -> list[str]:
    """List all registered service names."""
    return [schema.service for schema in METRICS_REGISTRY]
