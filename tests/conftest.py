"""Test fixtures for Pulse SDK tests."""

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
