"""Queue adapters for the Pulse SDK."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from pulse.exceptions import EmitError
from pulse.models import MetricMessage

logger = logging.getLogger(__name__)


class QueueAdapter(ABC):
    """Abstract base class for queue adapters."""

    @abstractmethod
    def enqueue(self, message: MetricMessage) -> bool:
        """
        Enqueue a single metric message.

        Args:
            message: The metric message to enqueue

        Returns:
            True if successfully enqueued, False if rejected (duplicate or error)
        """
        pass

    @abstractmethod
    def enqueue_batch(self, messages: list[MetricMessage]) -> int:
        """
        Enqueue multiple metric messages.

        Args:
            messages: List of metric messages to enqueue

        Returns:
            Number of messages successfully enqueued
        """
        pass


class EQMAdapter(QueueAdapter):
    """
    Production adapter using Entity Queue Manager (Redis).

    Lazy-loads EQM to avoid import errors in test environments.
    """

    def __init__(self, queue_name: str) -> None:
        """
        Initialize the EQM adapter.

        Args:
            queue_name: Name of the Redis queue
        """
        self._queue_name = queue_name
        self._eqm: Optional[object] = None

    def _get_eqm(self) -> object:
        """Lazy-load EQM client."""
        if self._eqm is None:
            try:
                # Attempt to import EQM
                from eqm import EntityQueueManager  # type: ignore

                self._eqm = EntityQueueManager(queue_name=self._queue_name)
            except ImportError:
                raise EmitError(
                    "EQM library not installed. Install with: pip install eqm"
                )
        return self._eqm

    def enqueue(self, message: MetricMessage) -> bool:
        """
        Enqueue a single metric message via EQM.

        Args:
            message: The metric message to enqueue

        Returns:
            True if successfully enqueued, False if rejected
        """
        try:
            eqm = self._get_eqm()
            # EQM uses entity_id for deduplication
            result = eqm.enqueue(  # type: ignore
                entity_id=message.idempotency_key,
                payload=json.dumps(message.to_dict()),
            )
            return bool(result)
        except EmitError:
            raise
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return False

    def enqueue_batch(self, messages: list[MetricMessage]) -> int:
        """
        Enqueue multiple metric messages via EQM.

        Args:
            messages: List of metric messages to enqueue

        Returns:
            Number of messages successfully enqueued
        """
        success_count = 0
        for message in messages:
            if self.enqueue(message):
                success_count += 1
        return success_count


class MockQueueAdapter(QueueAdapter):
    """
    Test adapter with in-memory storage and dedup simulation.

    Useful for unit testing without Redis.
    """

    def __init__(self) -> None:
        """Initialize the mock adapter."""
        self.messages: list[MetricMessage] = []
        self.rejected_keys: list[str] = []
        self._seen_keys: set[str] = set()

    def enqueue(self, message: MetricMessage) -> bool:
        """
        Enqueue a message with dedup simulation.

        Args:
            message: The metric message to enqueue

        Returns:
            True if accepted, False if duplicate
        """
        if message.idempotency_key in self._seen_keys:
            self.rejected_keys.append(message.idempotency_key)
            return False

        self._seen_keys.add(message.idempotency_key)
        self.messages.append(message)
        return True

    def enqueue_batch(self, messages: list[MetricMessage]) -> int:
        """
        Enqueue multiple messages.

        Args:
            messages: List of metric messages to enqueue

        Returns:
            Number of messages successfully enqueued
        """
        success_count = 0
        for message in messages:
            if self.enqueue(message):
                success_count += 1
        return success_count

    def clear(self) -> None:
        """Clear all stored messages and seen keys."""
        self.messages.clear()
        self.rejected_keys.clear()
        self._seen_keys.clear()
