"""Data models for the Pulse SDK."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AirflowContext:
    """Context from Airflow for idempotency key generation."""

    dag_id: str
    task_id: str
    run_id: str

    @classmethod
    def from_airflow(cls) -> "AirflowContext":
        """
        Auto-detect context from the current Airflow task execution.

        Raises:
            RuntimeError: If not running inside an Airflow task
        """
        try:
            from airflow.operators.python import get_current_context
        except ImportError:
            raise RuntimeError(
                "Airflow is not installed. Install airflow or provide "
                "AirflowContext manually."
            )

        try:
            context = get_current_context()
        except Exception:
            raise RuntimeError(
                "Not running inside an Airflow task. Cannot auto-detect context. "
                "Provide AirflowContext manually for testing."
            )

        dag_run = context.get("dag_run")
        task_instance = context.get("task_instance") or context.get("ti")

        if dag_run is None or task_instance is None:
            raise RuntimeError(
                "Could not get dag_run or task_instance from Airflow context."
            )

        return cls(
            dag_id=task_instance.dag_id,
            task_id=task_instance.task_id,
            run_id=dag_run.run_id,
        )


@dataclass(frozen=True)
class MetricMessage:
    """Message to be sent to the queue."""

    timestamp: str
    metric_name: str
    value: float
    entity_id: str
    idempotency_key: str

    def to_dict(self) -> dict[str, Any]:
        """Convert the message to a dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "metric_name": self.metric_name,
            "value": self.value,
            "entity_id": self.entity_id,
            "idempotency_key": self.idempotency_key,
        }
