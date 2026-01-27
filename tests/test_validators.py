"""Tests for Pulse SDK validators."""

import pytest

from pulse import Metric, MetricType
from pulse.exceptions import ValidationError
from pulse.registry import MAX_ENTITY_ID_LENGTH, Owners, PulseQueues, ServiceSchema
from pulse.utils import validate_entity_id, validate_metric, validate_value


@pytest.fixture
def sample_service() -> ServiceSchema:
    """Create a sample service for testing."""
    return ServiceSchema(
        service="test",
        queue_name=PulseQueues.LEVERAGE_METRICS,
        owner=Owners.DATA_SCIENCE,
        metrics=(
            Metric(name="tagged", type=MetricType.COUNTER),
            Metric(name="latency_ms", type=MetricType.TIMING),
        ),
    )


class TestValidateMetric:
    """Tests for validate_metric function."""

    def test_validate_registered_metric(self, sample_service: ServiceSchema) -> None:
        """Test validating a registered metric."""
        tagged_metric = Metric(name="tagged", type=MetricType.COUNTER)
        # Should not raise
        validate_metric(tagged_metric, sample_service)

    def test_validate_unregistered_metric_raises(self, sample_service: ServiceSchema) -> None:
        """Test that unregistered metric raises ValidationError."""
        unknown_metric = Metric(name="unknown", type=MetricType.COUNTER)
        with pytest.raises(ValidationError) as exc_info:
            validate_metric(unknown_metric, sample_service)
        assert "not registered" in str(exc_info.value)

    def test_validate_none_metric_raises(self, sample_service: ServiceSchema) -> None:
        """Test that None metric raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_metric(None, sample_service)  # type: ignore
        assert "is required" in str(exc_info.value)

    def test_validate_metric_non_metric_object_raises(self, sample_service: ServiceSchema) -> None:
        """Test that non-Metric object raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_metric("tagged", sample_service)  # type: ignore
        assert "must be a Metric object" in str(exc_info.value)

    def test_validate_metric_int_raises(self, sample_service: ServiceSchema) -> None:
        """Test that integer raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_metric(123, sample_service)  # type: ignore
        assert "must be a Metric object" in str(exc_info.value)


class TestValidateValue:
    """Tests for validate_value function."""

    def test_validate_int(self) -> None:
        """Test validating an integer value."""
        assert validate_value(42) == 42.0

    def test_validate_float(self) -> None:
        """Test validating a float value."""
        assert validate_value(3.14) == 3.14

    def test_validate_zero(self) -> None:
        """Test validating zero."""
        assert validate_value(0) == 0.0

    def test_validate_negative(self) -> None:
        """Test validating negative value."""
        assert validate_value(-10.5) == -10.5

    def test_validate_none_raises(self) -> None:
        """Test that None raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_value(None)
        assert "cannot be None" in str(exc_info.value)

    def test_validate_string_raises(self) -> None:
        """Test that string raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_value("42")  # type: ignore
        assert "must be numeric" in str(exc_info.value)

    def test_validate_nan_raises(self) -> None:
        """Test that NaN raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_value(float("nan"))
        assert "cannot be NaN" in str(exc_info.value)

    def test_validate_positive_infinity_raises(self) -> None:
        """Test that positive infinity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_value(float("inf"))
        assert "cannot be infinite" in str(exc_info.value)

    def test_validate_negative_infinity_raises(self) -> None:
        """Test that negative infinity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_value(float("-inf"))
        assert "cannot be infinite" in str(exc_info.value)

    def test_validate_list_raises(self) -> None:
        """Test that list raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_value([1, 2, 3])  # type: ignore
        assert "must be numeric" in str(exc_info.value)


class TestValidateEntityId:
    """Tests for validate_entity_id function."""

    def test_validate_valid_entity_id(self) -> None:
        """Test validating a valid entity ID."""
        assert validate_entity_id("tx_123") == "tx_123"

    def test_validate_empty_entity_id_raises(self) -> None:
        """Test that empty entity_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_entity_id("")
        assert "cannot be empty" in str(exc_info.value)

    def test_validate_whitespace_entity_id_raises(self) -> None:
        """Test that whitespace entity_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_entity_id("   ")
        assert "cannot be empty" in str(exc_info.value)

    def test_validate_none_entity_id_raises(self) -> None:
        """Test that None entity_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_entity_id(None)
        assert "is required" in str(exc_info.value)

    def test_validate_entity_id_too_long_raises(self) -> None:
        """Test that too long entity_id raises ValidationError."""
        long_id = "a" * (MAX_ENTITY_ID_LENGTH + 1)
        with pytest.raises(ValidationError) as exc_info:
            validate_entity_id(long_id)
        assert "maximum length" in str(exc_info.value)

    def test_validate_converts_int_to_string(self) -> None:
        """Test that integer entity_id is converted to string."""
        assert validate_entity_id(12345) == "12345"
