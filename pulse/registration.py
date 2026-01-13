"""Registration loader for the Pulse SDK."""

from pathlib import Path
from typing import Any, Optional

import yaml

from pulse.constants import MetricType
from pulse.exceptions import ConfigurationError
from pulse.models import MetricDefinition, ServiceRegistration


class RegistrationLoader:
    """Loads and validates service registration from YAML files."""

    # Default registry path is relative to this module
    DEFAULT_REGISTRY_PATH = Path(__file__).parent / "registry"

    def __init__(self, registry_path: Optional[Path] = None) -> None:
        """
        Initialize the loader.

        Args:
            registry_path: Optional custom path to registry directory
        """
        self._registry_path = registry_path or self.DEFAULT_REGISTRY_PATH

    def load(self, service: str) -> ServiceRegistration:
        """
        Load and validate a service registration.

        Args:
            service: The service name to load

        Returns:
            The validated ServiceRegistration

        Raises:
            ConfigurationError: If the service is not registered or config is invalid
        """
        if not service:
            raise ConfigurationError("Service name cannot be empty")

        if not isinstance(service, str):
            raise ConfigurationError(
                f"Service name must be a string, got {type(service).__name__}"
            )

        config_path = self._registry_path / f"{service}.yaml"

        if not config_path.exists():
            raise ConfigurationError(
                f"Service '{service}' is not registered. "
                f"Expected config at: {config_path}"
            )

        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {config_path}: {e}")

        return self._validate_config(config, service, config_path)

    def _validate_config(
        self,
        config: Any,
        expected_service: str,
        config_path: Path,
    ) -> ServiceRegistration:
        """
        Validate the configuration and build a ServiceRegistration.

        Args:
            config: The loaded YAML config
            expected_service: Expected service name (from filename)
            config_path: Path to the config file (for error messages)

        Returns:
            Validated ServiceRegistration

        Raises:
            ConfigurationError: If validation fails
        """
        if not isinstance(config, dict):
            raise ConfigurationError(
                f"Invalid config format in {config_path}: expected dict"
            )

        # Validate required fields
        required_fields = ["service", "owner", "queue_name", "metrics"]
        for field in required_fields:
            if field not in config:
                raise ConfigurationError(
                    f"Missing required field '{field}' in {config_path}"
                )

        # Validate service name matches filename
        if config["service"] != expected_service:
            raise ConfigurationError(
                f"Service name mismatch: config says '{config['service']}' "
                f"but filename is '{expected_service}.yaml'"
            )

        # Validate metrics
        metrics_list = config.get("metrics", [])
        if not isinstance(metrics_list, list):
            raise ConfigurationError(
                f"'metrics' must be a list in {config_path}"
            )

        metrics = self._parse_metrics(metrics_list, config_path)

        return ServiceRegistration(
            service=config["service"],
            owner=config["owner"],
            queue_name=config["queue_name"],
            metrics=metrics,
        )

    def _parse_metrics(
        self,
        metrics_list: list[Any],
        config_path: Path,
    ) -> dict[str, MetricDefinition]:
        """
        Parse and validate metrics from config.

        Args:
            metrics_list: List of metric configurations
            config_path: Path to the config file (for error messages)

        Returns:
            Dictionary of metric name to MetricDefinition

        Raises:
            ConfigurationError: If validation fails
        """
        metrics: dict[str, MetricDefinition] = {}
        seen_names: set[str] = set()

        for i, metric_config in enumerate(metrics_list):
            if not isinstance(metric_config, dict):
                raise ConfigurationError(
                    f"Metric at index {i} must be a dict in {config_path}"
                )

            # Validate required metric fields
            if "name" not in metric_config:
                raise ConfigurationError(
                    f"Metric at index {i} missing 'name' in {config_path}"
                )

            if "type" not in metric_config:
                raise ConfigurationError(
                    f"Metric at index {i} missing 'type' in {config_path}"
                )

            name = metric_config["name"]

            # Check for duplicates
            if name in seen_names:
                raise ConfigurationError(
                    f"Duplicate metric name '{name}' in {config_path}"
                )
            seen_names.add(name)

            # Validate metric type
            type_str = metric_config["type"]
            try:
                metric_type = MetricType(type_str)
            except ValueError:
                valid_types = [t.value for t in MetricType]
                raise ConfigurationError(
                    f"Invalid metric type '{type_str}' for metric '{name}'. "
                    f"Valid types: {valid_types}"
                )

            # Validate deduplicate field
            deduplicate = metric_config.get("deduplicate", True)
            if not isinstance(deduplicate, bool):
                raise ConfigurationError(
                    f"'deduplicate' must be a boolean for metric '{name}' "
                    f"in {config_path}, got {type(deduplicate).__name__}"
                )

            description = metric_config.get("description", "")

            metrics[name] = MetricDefinition(
                name=name,
                metric_type=metric_type,
                deduplicate=deduplicate,
                description=description,
            )

        return metrics
