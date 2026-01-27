"""Tests for Pulse SDK registration loader."""

import pytest

from pulse.constants import MetricType
from pulse.exceptions import ConfigurationError
from pulse.registration import RegistrationLoader
from pulse.registry import (
    METRICS_REGISTRY,
    Metric,
    Owners,
    PulseQueues,
    ServiceSchema,
    get_service_registry,
    list_services,
)


class TestRegistrationLoader:
    """Tests for RegistrationLoader."""

    def test_load_valid_registration(self) -> None:
        """Test loading a valid service registration."""
        loader = RegistrationLoader()

        registration = loader.load("leverage")

        assert registration.service == "leverage"
        assert registration.owner == "data_science"
        assert registration.queue_name == "PULSE_LEVERAGE_METRICS_QUEUE"
        assert len(registration.metrics) == 2
        assert "tagged" in registration.metrics
        assert "match_latency_ms" in registration.metrics

    def test_load_metric_types_correctly(self) -> None:
        """Test that metric types are loaded correctly."""
        loader = RegistrationLoader()

        registration = loader.load("leverage")

        assert registration.metrics["tagged"].metric_type == MetricType.COUNTER
        assert registration.metrics["match_latency_ms"].metric_type == MetricType.TIMING

    def test_load_deduplicate_correctly(self) -> None:
        """Test that deduplicate flag is loaded correctly."""
        loader = RegistrationLoader()

        registration = loader.load("leverage")

        assert registration.metrics["tagged"].deduplicate is True
        assert registration.metrics["match_latency_ms"].deduplicate is False

    def test_load_nonexistent_service_raises(self) -> None:
        """Test that loading non-existent service raises ConfigurationError."""
        loader = RegistrationLoader()

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("nonexistent")

        assert "not registered" in str(exc_info.value)

    def test_load_empty_service_name_raises(self) -> None:
        """Test that empty service name raises ConfigurationError."""
        loader = RegistrationLoader()

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("")

        assert "cannot be empty" in str(exc_info.value)


class TestServiceSchema:
    """Tests for ServiceSchema."""

    def test_create_service_schema(self) -> None:
        """Test creating a ServiceSchema."""
        schema = ServiceSchema(
            service="test_service",
            queue_name=PulseQueues.LEVERAGE_METRICS,
            owner=Owners.DATA_SCIENCE,
            metrics=(
                Metric(name="test_metric", type=MetricType.COUNTER),
            ),
        )

        assert schema.service == "test_service"
        assert schema.queue_name == PulseQueues.LEVERAGE_METRICS
        assert schema.owner == Owners.DATA_SCIENCE
        assert len(schema.metrics) == 1

    def test_get_metric(self) -> None:
        """Test getting a metric by name."""
        schema = ServiceSchema(
            service="test",
            queue_name=PulseQueues.LEVERAGE_METRICS,
            owner=Owners.DATA_SCIENCE,
            metrics=(
                Metric(name="metric_a", type=MetricType.COUNTER),
                Metric(name="metric_b", type=MetricType.GAUGE),
            ),
        )

        metric = schema.get_metric("metric_a")
        assert metric is not None
        assert metric.name == "metric_a"

        missing = schema.get_metric("nonexistent")
        assert missing is None

    def test_has_metric(self) -> None:
        """Test checking if a metric exists."""
        schema = ServiceSchema(
            service="test",
            queue_name=PulseQueues.LEVERAGE_METRICS,
            owner=Owners.DATA_SCIENCE,
            metrics=(
                Metric(name="metric_a", type=MetricType.COUNTER),
            ),
        )

        assert schema.has_metric("metric_a") is True
        assert schema.has_metric("nonexistent") is False


class TestMetric:
    """Tests for Metric dataclass."""

    def test_create_metric_with_defaults(self) -> None:
        """Test creating a metric with default values."""
        metric = Metric(name="test")

        assert metric.name == "test"
        assert metric.type == MetricType.COUNTER
        assert metric.deduplicate is True
        assert metric.description == ""

    def test_create_metric_with_all_fields(self) -> None:
        """Test creating a metric with all fields specified."""
        metric = Metric(
            name="latency",
            type=MetricType.TIMING,
            deduplicate=False,
            description="Request latency",
        )

        assert metric.name == "latency"
        assert metric.type == MetricType.TIMING
        assert metric.deduplicate is False
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
