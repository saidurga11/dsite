"""Metrics registry and constants for the Pulse SDK."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


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
    description: str = ""


@dataclass(frozen=True)
class ServiceSchema:
    """Schema for a service registration."""

    service: str
    queue_name: PulseQueues
    owner: Owners
    metrics: tuple[Metric, ...] = field(default_factory=tuple)

    def get_metric(self, metric: "Metric") -> Optional["Metric"]:
        """Get a metric if it's registered for this service."""
        for m in self.metrics:
            if m.name == metric.name:
                return m
        return None

    def has_metric(self, metric: "Metric") -> bool:
        """Check if a metric is registered."""
        return self.get_metric(metric) is not None


# =============================================================================
# METRIC DEFINITIONS - Define metrics as class constants
# =============================================================================


class LeverageMetrics:
    """Metrics for the leverage service."""

    TAGGED = Metric(name="tagged")
    MATCH_LATENCY_MS = Metric(name="match_latency_ms")


# =============================================================================
# METRICS REGISTRY - Register services with their metrics
# =============================================================================

METRICS_REGISTRY: list[ServiceSchema] = [
    ServiceSchema(
        service="leverage",
        queue_name=PulseQueues.LEVERAGE_METRICS,
        owner=Owners.DATA_SCIENCE,
        metrics=(
            LeverageMetrics.TAGGED,
            LeverageMetrics.MATCH_LATENCY_MS,
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
