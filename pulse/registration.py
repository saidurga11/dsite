"""Registration loader for the Pulse SDK."""

from typing import Optional

from pulse.exceptions import ConfigurationError
from pulse.models import MetricDefinition, ServiceRegistration
from pulse.registry import get_service_registry, list_services


class RegistrationLoader:
    """Loads service registration from the Python-based registry."""

    def __init__(self) -> None:
        """Initialize the loader."""
        pass

    def load(self, service: str) -> ServiceRegistration:
        """
        Load a service registration.

        Args:
            service: The service name to load

        Returns:
            The ServiceRegistration

        Raises:
            ConfigurationError: If the service is not registered
        """
        if not service:
            raise ConfigurationError("Service name cannot be empty")

        if not isinstance(service, str):
            raise ConfigurationError(
                f"Service name must be a string, got {type(service).__name__}"
            )

        schema = get_service_registry(service)

        if schema is None:
            available = list_services()
            raise ConfigurationError(
                f"Service '{service}' is not registered. "
                f"Available services: {available}"
            )

        # Convert Metric objects to MetricDefinition dict
        metrics: dict[str, MetricDefinition] = {}
        for metric in schema.metrics:
            metrics[metric.name] = MetricDefinition(
                name=metric.name,
                metric_type=metric.type,
                deduplicate=metric.deduplicate,
                description=metric.description,
            )

        return ServiceRegistration(
            service=schema.service,
            owner=schema.owner.value,
            queue_name=schema.queue_name.value,
            metrics=metrics,
        )
