"""Tests for Pulse SDK validators."""

import pytest

from pulse.constants import (
    MAX_ENTITY_ID_LENGTH,
    MAX_METRIC_NAME_LENGTH,
    MetricType,
)
from pulse.exceptions import ValidationError
from pulse.models import MetricDefinition
from pulse.validators import (
    EntityIdValidator,
    MetricValidator,
    ValueValidator,
)


class TestMetricValidator:
    """Tests for MetricValidator."""

    @pytest.fixture
    def registered_metrics(self) -> dict[str, MetricDefinition]:
        """Create sample registered metrics."""
        return {
            "tagged": MetricDefinition(
                name="tagged",
                metric_type=MetricType.COUNTER,
                deduplicate=True,
            ),
            "latency_ms": MetricDefinition(
                name="latency_ms",
                metric_type=MetricType.TIMING,
                deduplicate=False,
            ),
        }

    @pytest.fixture
    def validator(
        self, registered_metrics: dict[str, MetricDefinition]
    ) -> MetricValidator:
        """Create a MetricValidator with registered metrics."""
        return MetricValidator(registered_metrics)

    def test_validate_registered_metric(self, validator: MetricValidator) -> None:
        """Test validating a registered metric name."""
        result = validator.validate("tagged")

        assert result.name == "tagged"
        assert result.metric_type == MetricType.COUNTER

    def test_validate_unregistered_metric_raises(
        self, validator: MetricValidator
    ) -> None:
        """Test that unregistered metric raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("unknown_metric")

        assert "not registered" in str(exc_info.value)

    def test_validate_empty_metric_name_raises(
        self, validator: MetricValidator
    ) -> None:
        """Test that empty metric name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("")

        assert "cannot be empty" in str(exc_info.value)

    def test_validate_metric_name_too_long_raises(
        self, validator: MetricValidator
    ) -> None:
        """Test that metric name exceeding max length raises ValidationError."""
        long_name = "a" * (MAX_METRIC_NAME_LENGTH + 1)

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(long_name)

        assert "exceeds maximum length" in str(exc_info.value)

    def test_validate_metric_name_invalid_chars_raises(
        self, validator: MetricValidator
    ) -> None:
        """Test that metric name with invalid characters raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("invalid metric!")

        assert "invalid characters" in str(exc_info.value)

    def test_validate_metric_name_starting_with_number_raises(
        self, validator: MetricValidator
    ) -> None:
        """Test that metric name starting with number raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate("123metric")

        assert "invalid characters" in str(exc_info.value)

    def test_validate_metric_name_non_string_raises(
        self, validator: MetricValidator
    ) -> None:
        """Test that non-string metric name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(123)  # type: ignore

        assert "must be a string" in str(exc_info.value)


class TestValueValidator:
    """Tests for ValueValidator."""

    def test_validate_int(self) -> None:
        """Test validating an integer value."""
        result = ValueValidator.validate(42)

        assert result == 42.0
        assert isinstance(result, float)

    def test_validate_float(self) -> None:
        """Test validating a float value."""
        result = ValueValidator.validate(3.14)

        assert result == 3.14

    def test_validate_zero(self) -> None:
        """Test validating zero."""
        result = ValueValidator.validate(0)

        assert result == 0.0

    def test_validate_negative(self) -> None:
        """Test validating negative value."""
        result = ValueValidator.validate(-10.5)

        assert result == -10.5

    def test_validate_none_raises(self) -> None:
        """Test that None value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ValueValidator.validate(None)

        assert "cannot be None" in str(exc_info.value)

    def test_validate_string_raises(self) -> None:
        """Test that string value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ValueValidator.validate("42")

        assert "must be numeric" in str(exc_info.value)

    def test_validate_nan_raises(self) -> None:
        """Test that NaN value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ValueValidator.validate(float("nan"))

        assert "cannot be NaN" in str(exc_info.value)

    def test_validate_positive_infinity_raises(self) -> None:
        """Test that positive infinity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ValueValidator.validate(float("inf"))

        assert "cannot be infinite" in str(exc_info.value)

    def test_validate_negative_infinity_raises(self) -> None:
        """Test that negative infinity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ValueValidator.validate(float("-inf"))

        assert "cannot be infinite" in str(exc_info.value)

    def test_validate_list_raises(self) -> None:
        """Test that list value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ValueValidator.validate([1, 2, 3])

        assert "must be numeric" in str(exc_info.value)


class TestEntityIdValidator:
    """Tests for EntityIdValidator."""

    @pytest.fixture
    def dedup_metric(self) -> MetricDefinition:
        """Create a metric with deduplication enabled."""
        return MetricDefinition(
            name="tagged",
            metric_type=MetricType.COUNTER,
            deduplicate=True,
        )

    @pytest.fixture
    def non_dedup_metric(self) -> MetricDefinition:
        """Create a metric with deduplication disabled."""
        return MetricDefinition(
            name="latency_ms",
            metric_type=MetricType.TIMING,
            deduplicate=False,
        )

    def test_validate_valid_entity_id_with_dedup(
        self, dedup_metric: MetricDefinition
    ) -> None:
        """Test validating a valid entity_id when dedup is enabled."""
        result = EntityIdValidator.validate("tx_abc123", dedup_metric)

        assert result == "tx_abc123"

    def test_validate_empty_entity_id_when_dedup_enabled_raises(
        self, dedup_metric: MetricDefinition
    ) -> None:
        """Test that empty entity_id raises ValidationError when dedup enabled."""
        with pytest.raises(ValidationError) as exc_info:
            EntityIdValidator.validate("", dedup_metric)

        assert "cannot be empty" in str(exc_info.value)

    def test_validate_whitespace_entity_id_when_dedup_enabled_raises(
        self, dedup_metric: MetricDefinition
    ) -> None:
        """Test that whitespace entity_id raises ValidationError when dedup enabled."""
        with pytest.raises(ValidationError) as exc_info:
            EntityIdValidator.validate("   ", dedup_metric)

        assert "cannot be empty" in str(exc_info.value)

    def test_validate_none_entity_id_when_dedup_enabled_raises(
        self, dedup_metric: MetricDefinition
    ) -> None:
        """Test that None entity_id raises ValidationError when dedup enabled."""
        with pytest.raises(ValidationError) as exc_info:
            EntityIdValidator.validate(None, dedup_metric)

        assert "is required" in str(exc_info.value)

    def test_validate_empty_entity_id_when_dedup_disabled(
        self, non_dedup_metric: MetricDefinition
    ) -> None:
        """Test that empty entity_id is allowed when dedup disabled."""
        result = EntityIdValidator.validate("", non_dedup_metric)

        assert result == ""

    def test_validate_none_entity_id_when_dedup_disabled(
        self, non_dedup_metric: MetricDefinition
    ) -> None:
        """Test that None entity_id is allowed when dedup disabled."""
        result = EntityIdValidator.validate(None, non_dedup_metric)

        assert result == ""

    def test_validate_entity_id_too_long_raises(
        self, dedup_metric: MetricDefinition
    ) -> None:
        """Test that entity_id exceeding max length raises ValidationError."""
        long_id = "x" * (MAX_ENTITY_ID_LENGTH + 1)

        with pytest.raises(ValidationError) as exc_info:
            EntityIdValidator.validate(long_id, dedup_metric)

        assert "exceeds maximum length" in str(exc_info.value)

    def test_validate_converts_int_to_string(
        self, dedup_metric: MetricDefinition
    ) -> None:
        """Test that integer entity_id is converted to string."""
        result = EntityIdValidator.validate(12345, dedup_metric)  # type: ignore

        assert result == "12345"

    def test_validate_valid_entity_id_when_dedup_disabled(
        self, non_dedup_metric: MetricDefinition
    ) -> None:
        """Test validating valid entity_id when dedup disabled."""
        result = EntityIdValidator.validate("tx_abc123", non_dedup_metric)

        assert result == "tx_abc123"
