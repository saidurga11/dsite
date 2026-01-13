"""Test fixtures for Pulse SDK tests."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from pulse import AirflowContext, MockQueueAdapter


@pytest.fixture
def mock_queue_adapter() -> MockQueueAdapter:
    """Create a mock queue adapter for testing."""
    return MockQueueAdapter()


@pytest.fixture
def sample_airflow_context() -> AirflowContext:
    """Create a sample Airflow context for testing."""
    return AirflowContext(
        dag_id="test_dag",
        task_id="test_task",
        run_id="scheduled__2026-01-08T14:00:00",
    )


@pytest.fixture
def temp_registry_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test registry files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def valid_leverage_yaml() -> str:
    """Return valid leverage.yaml content."""
    return """service: leverage
owner: data_science
queue_name: PULSE_LEVERAGE_METRICS_QUEUE

metrics:
  - name: tagged
    type: counter
    deduplicate: true
    description: "Transactions processed by tagging"

  - name: match_latency_ms
    type: timing
    deduplicate: false
    description: "Match latency in milliseconds"
"""


@pytest.fixture
def valid_test_service_yaml() -> str:
    """Return valid test_service.yaml content."""
    return """service: test_service
owner: test_team
queue_name: TEST_QUEUE

metrics:
  - name: test_counter
    type: counter
    deduplicate: true
    description: "Test counter metric"

  - name: test_gauge
    type: gauge
    deduplicate: true
    description: "Test gauge metric"

  - name: test_timing
    type: timing
    deduplicate: false
    description: "Test timing metric"
"""


@pytest.fixture
def registry_with_test_service(
    temp_registry_dir: Path, valid_test_service_yaml: str
) -> Path:
    """Create a registry directory with a test service."""
    config_path = temp_registry_dir / "test_service.yaml"
    config_path.write_text(valid_test_service_yaml)
    return temp_registry_dir


@pytest.fixture
def registry_with_leverage(
    temp_registry_dir: Path, valid_leverage_yaml: str
) -> Path:
    """Create a registry directory with the leverage service."""
    config_path = temp_registry_dir / "leverage.yaml"
    config_path.write_text(valid_leverage_yaml)
    return temp_registry_dir
