"""Tests for Pulse SDK registry."""

import pytest

from pulse import Metric, MetricType
from pulse.registry import (
    METRICS_REGISTRY,
    Owners,
    PulseQueues,
    ServiceSchema,
    get_service_registry,
    list_services,
)


class TestServiceSchema:
    """Tests for ServiceSchema."""

    def test_create_service_schema(self) -> None:
        """Test creating a ServiceSchema."""
        schema = ServiceSchema(
            service="test_service",
            queue_name=PulseQueues.LEVERAGE_METRICS,
            owner=Owners.DATA_SCIENCE,
            metrics=(Metric(name="test_metric", type=MetricType.COUNTER),),
        )

        assert schema.service == "test_service"
        assert schema.queue_name == PulseQueues.LEVERAGE_METRICS
        assert schema.owner == Owners.DATA_SCIENCE
        assert len(schema.metrics) == 1

    def test_get_metric(self) -> None:
        """Test getting a metric by Metric object."""
        metric_a = Metric(name="metric_a", type=MetricType.COUNTER)
        metric_b = Metric(name="metric_b", type=MetricType.GAUGE)
        schema = ServiceSchema(
            service="test",
            queue_name=PulseQueues.LEVERAGE_METRICS,
            owner=Owners.DATA_SCIENCE,
            metrics=(metric_a, metric_b),
        )

        found = schema.get_metric(metric_a)
        assert found is not None
        assert found.name == "metric_a"

        nonexistent = Metric(name="nonexistent", type=MetricType.COUNTER)
        missing = schema.get_metric(nonexistent)
        assert missing is None

    def test_has_metric(self) -> None:
        """Test checking if a metric exists."""
        metric_a = Metric(name="metric_a", type=MetricType.COUNTER)
        schema = ServiceSchema(
            service="test",
            queue_name=PulseQueues.LEVERAGE_METRICS,
            owner=Owners.DATA_SCIENCE,
            metrics=(metric_a,),
        )

        assert schema.has_metric(metric_a) is True
        nonexistent = Metric(name="nonexistent", type=MetricType.COUNTER)
        assert schema.has_metric(nonexistent) is False


class TestMetric:
    """Tests for Metric dataclass."""

    def test_create_metric_with_defaults(self) -> None:
        """Test creating a metric with default values."""
        metric = Metric(name="test")

        assert metric.name == "test"
        assert metric.type == MetricType.COUNTER
        assert metric.description == ""

    def test_create_metric_with_all_fields(self) -> None:
        """Test creating a metric with all fields specified."""
        metric = Metric(
            name="latency",
            type=MetricType.TIMING,
            description="Request latency",
        )

        assert metric.name == "latency"
        assert metric.type == MetricType.TIMING
        assert metric.description == "Request latency"


class TestRegistryFunctions:
    """Tests for registry helper functions."""

    def test_get_service_registry_existing(self) -> None:
        """Test getting an existing service."""
        schema = get_service_registry("leverage")

        assert schema is not None
        assert schema.service == "leverage"

    def test_get_service_registry_nonexistent(self) -> None:
        """Test getting a non-existent service."""
        schema = get_service_registry("nonexistent")

        assert schema is None

    def test_list_services(self) -> None:
        """Test listing all registered services."""
        services = list_services()

        assert isinstance(services, list)
        assert "leverage" in services


class TestMetricsRegistry:
    """Tests for the METRICS_REGISTRY."""

    def test_registry_is_list(self) -> None:
        """Test that METRICS_REGISTRY is a list."""
        assert isinstance(METRICS_REGISTRY, list)

    def test_registry_contains_valid_schemas(self) -> None:
        """Test that all entries in registry are valid ServiceSchemas."""
        for schema in METRICS_REGISTRY:
            assert isinstance(schema, ServiceSchema)
            assert schema.service
            assert schema.queue_name
            assert schema.owner

    def test_leverage_service_in_registry(self) -> None:
        """Test that leverage service is in the registry."""
        services = [s.service for s in METRICS_REGISTRY]
        assert "leverage" in services
