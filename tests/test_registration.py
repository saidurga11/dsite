"""Tests for Pulse SDK registration loader."""

from pathlib import Path

import pytest

from pulse.constants import MetricType
from pulse.exceptions import ConfigurationError
from pulse.registration import RegistrationLoader


class TestRegistrationLoader:
    """Tests for RegistrationLoader."""

    def test_load_valid_registration(
        self, registry_with_test_service: Path
    ) -> None:
        """Test loading a valid service registration."""
        loader = RegistrationLoader(registry_with_test_service)

        registration = loader.load("test_service")

        assert registration.service == "test_service"
        assert registration.owner == "test_team"
        assert registration.queue_name == "TEST_QUEUE"
        assert len(registration.metrics) == 3
        assert "test_counter" in registration.metrics
        assert "test_gauge" in registration.metrics
        assert "test_timing" in registration.metrics

    def test_load_metric_types_correctly(
        self, registry_with_test_service: Path
    ) -> None:
        """Test that metric types are loaded correctly."""
        loader = RegistrationLoader(registry_with_test_service)

        registration = loader.load("test_service")

        assert registration.metrics["test_counter"].metric_type == MetricType.COUNTER
        assert registration.metrics["test_gauge"].metric_type == MetricType.GAUGE
        assert registration.metrics["test_timing"].metric_type == MetricType.TIMING

    def test_load_deduplicate_correctly(
        self, registry_with_test_service: Path
    ) -> None:
        """Test that deduplicate flag is loaded correctly."""
        loader = RegistrationLoader(registry_with_test_service)

        registration = loader.load("test_service")

        assert registration.metrics["test_counter"].deduplicate is True
        assert registration.metrics["test_gauge"].deduplicate is True
        assert registration.metrics["test_timing"].deduplicate is False

    def test_load_nonexistent_service_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that loading non-existent service raises ConfigurationError."""
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("nonexistent")

        assert "not registered" in str(exc_info.value)

    def test_load_empty_service_name_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that empty service name raises ConfigurationError."""
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("")

        assert "cannot be empty" in str(exc_info.value)

    def test_load_missing_required_field_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that missing required field raises ConfigurationError."""
        # Create config missing 'owner'
        config = """service: test_service
queue_name: TEST_QUEUE
metrics:
  - name: test
    type: counter
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("test_service")

        assert "Missing required field 'owner'" in str(exc_info.value)

    def test_load_service_name_mismatch_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that service name mismatch raises ConfigurationError."""
        config = """service: wrong_name
owner: test_team
queue_name: TEST_QUEUE
metrics:
  - name: test
    type: counter
"""
        (temp_registry_dir / "my_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("my_service")

        assert "Service name mismatch" in str(exc_info.value)

    def test_load_invalid_metric_type_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that invalid metric type raises ConfigurationError."""
        config = """service: test_service
owner: test_team
queue_name: TEST_QUEUE
metrics:
  - name: test
    type: invalid_type
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("test_service")

        assert "Invalid metric type" in str(exc_info.value)

    def test_load_duplicate_metric_names_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that duplicate metric names raise ConfigurationError."""
        config = """service: test_service
owner: test_team
queue_name: TEST_QUEUE
metrics:
  - name: duplicate_name
    type: counter
  - name: duplicate_name
    type: gauge
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("test_service")

        assert "Duplicate metric name" in str(exc_info.value)

    def test_load_invalid_deduplicate_value_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that invalid deduplicate value raises ConfigurationError."""
        config = """service: test_service
owner: test_team
queue_name: TEST_QUEUE
metrics:
  - name: test
    type: counter
    deduplicate: "yes"
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("test_service")

        assert "must be a boolean" in str(exc_info.value)

    def test_load_metric_missing_name_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that metric missing name raises ConfigurationError."""
        config = """service: test_service
owner: test_team
queue_name: TEST_QUEUE
metrics:
  - type: counter
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("test_service")

        assert "missing 'name'" in str(exc_info.value)

    def test_load_metric_missing_type_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that metric missing type raises ConfigurationError."""
        config = """service: test_service
owner: test_team
queue_name: TEST_QUEUE
metrics:
  - name: test
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("test_service")

        assert "missing 'type'" in str(exc_info.value)

    def test_load_invalid_yaml_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that invalid YAML raises ConfigurationError."""
        config = """this is: not: valid: yaml:
  - [[[
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("test_service")

        assert "Invalid YAML" in str(exc_info.value)

    def test_load_deduplicate_defaults_to_true(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that deduplicate defaults to True when not specified."""
        config = """service: test_service
owner: test_team
queue_name: TEST_QUEUE
metrics:
  - name: test
    type: counter
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        registration = loader.load("test_service")

        assert registration.metrics["test"].deduplicate is True

    def test_load_description_defaults_to_empty(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that description defaults to empty string when not specified."""
        config = """service: test_service
owner: test_team
queue_name: TEST_QUEUE
metrics:
  - name: test
    type: counter
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        registration = loader.load("test_service")

        assert registration.metrics["test"].description == ""

    def test_load_with_description(
        self, temp_registry_dir: Path
    ) -> None:
        """Test loading metric with description."""
        config = """service: test_service
owner: test_team
queue_name: TEST_QUEUE
metrics:
  - name: test
    type: counter
    description: "This is a test metric"
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        registration = loader.load("test_service")

        assert registration.metrics["test"].description == "This is a test metric"

    def test_load_uses_default_registry_path(self) -> None:
        """Test that loader uses default registry path when none specified."""
        loader = RegistrationLoader()

        # The default path should be set to the registry directory
        assert loader._registry_path.name == "registry"
        assert loader._registry_path.parent.name == "pulse"

    def test_load_metrics_not_list_raises(
        self, temp_registry_dir: Path
    ) -> None:
        """Test that metrics not being a list raises ConfigurationError."""
        config = """service: test_service
owner: test_team
queue_name: TEST_QUEUE
metrics:
  test: counter
"""
        (temp_registry_dir / "test_service.yaml").write_text(config)
        loader = RegistrationLoader(temp_registry_dir)

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load("test_service")

        assert "'metrics' must be a list" in str(exc_info.value)
