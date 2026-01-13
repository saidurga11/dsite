"""Constants and enums for the Pulse SDK."""

import re
from enum import Enum


class MetricType(str, Enum):
    """Supported metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    TIMING = "timing"


# Validation limits
MAX_METRIC_NAME_LENGTH = 255
MAX_TAG_KEY_LENGTH = 64
MAX_TAG_VALUE_LENGTH = 256
MAX_TAGS_PER_METRIC = 20
MAX_ENTITY_ID_LENGTH = 512

# Metric name must start with letter, then letters/numbers/underscores/dots/hyphens
METRIC_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.\-]*$")
