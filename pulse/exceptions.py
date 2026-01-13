"""Custom exceptions for the Pulse SDK."""


class PulseError(Exception):
    """Base exception for all Pulse SDK errors."""

    pass


class ConfigurationError(PulseError):
    """
    Registration or setup issues.

    Raised when:
    - Service is not registered
    - Configuration file is invalid
    - Required fields are missing

    These errors should fail fast during initialization.
    """

    pass


class ValidationError(PulseError):
    """
    Invalid emit parameters.

    Raised when:
    - Metric name is invalid or unregistered
    - Value is not numeric or is NaN/Inf
    - Tags are invalid
    - Entity ID is missing when required

    These errors should fail fast during emit.
    """

    pass


class EmitError(PulseError):
    """
    Infrastructure errors during emit.

    Raised when:
    - Redis is unavailable
    - Queue operation fails

    These errors are logged but not raised to the caller.
    The emit() method returns False instead of raising.
    """

    pass
