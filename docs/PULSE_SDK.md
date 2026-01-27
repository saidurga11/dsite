# Pulse SDK Documentation

## Overview
The Pulse SDK allows your Airflow DAGs to emit operational metrics to PostgreSQL (`monitoring_source_metrics` table) for visualization in Grafana.

**Use case:** Track transaction counts, processing metrics, or any numeric values you want to monitor over time.

---

## Setup: Register a New Service

You need to update the Python registry and create an EQM config file.

### Step 1: Add Service to Python Registry

File: `pulse/registry.py`

Example (this is our actual leverage registration):

```python
class PulseQueues(str, Enum):
    """Available Pulse queues."""
    LEVERAGE_METRICS = "PULSE_LEVERAGE_METRICS_QUEUE"
    # Add more queues as needed

class Owners(str, Enum):
    """Service owners."""
    DATA_SCIENCE = "data_science"
    MLE = "mle"
    DATA_ENGINEERING = "data_engineering"

# Define metrics as class constants for type-safety and IDE autocomplete
class LeverageMetrics:
    """Metrics for the leverage service."""
    TAGGED = Metric(name="tagged", type=MetricType.COUNTER)
    MATCH_LATENCY_MS = Metric(name="match_latency_ms", type=MetricType.TIMING)

METRICS_REGISTRY: list[ServiceSchema] = [
    ServiceSchema(
        service="leverage",
        queue_name=PulseQueues.LEVERAGE_METRICS,
        owner=Owners.DATA_SCIENCE,
        metrics=(
            LeverageMetrics.TAGGED,
            LeverageMetrics.MATCH_LATENCY_MS,
        ),
    ),
]
```

**Field Reference:**

| Field | Required | Description |
|-------|----------|-------------|
| `service` | Yes | Must match `AggregationMonitoringService(service="...")` in your code |
| `owner` | Yes | Team that owns this service (e.g., `Owners.DATA_SCIENCE`, `Owners.DATA_ENGINEERING`) |
| `queue_name` | Yes | Queue from `PulseQueues` enum. Pattern: `PULSE_{SERVICE}_METRICS_QUEUE` |
| `metrics` | Yes | Tuple of Metric constants from your metrics class |
| `Metric.name` | Yes | Metric name (e.g., `"tagged"`) |
| `Metric.type` | No | `MetricType.COUNTER` (default), `GAUGE`, or `TIMING` |
| `Metric.description` | No | Human-readable description |

### Step 2: Create EQM Configuration

File: `data_db_utils/entity_queue_manager/queue_managers_configs/{service}_metrics_config.yaml`

Example:

```yaml
QueueManagerConfigurations:
  name: PULSE_LEVERAGE
  queues:
    - PULSE_LEVERAGE_METRICS_QUEUE
  entity_identifier_field: row_id
  max_ttl_time: 2592000
```

**Field Reference:**

| Field | Value | Why |
|-------|-------|-----|
| `name` | `PULSE_LEVERAGE` | Manager identifier (prefix of queue name) |
| `queues` | `[PULSE_LEVERAGE_METRICS_QUEUE]` | Must match `queue_name` in registry exactly |
| `entity_identifier_field` | `row_id` | Always use `row_id`. Enables deduplication on DAG retries |
| `max_ttl_time` | `2592000` | 30 days in seconds. Messages expire if not consumed |

### Step 3: Submit PR

Create PR with both changes. After merge, the consumer DAG automatically discovers your queue.

---

## Usage: Record Metrics in Your DAG

### Basic Pattern

```python
from pulse import AggregationMonitoringService
from pulse.registry import LeverageMetrics

def process_transactions(**context):
    # 1. Initialize service (Airflow context auto-detected)
    monitor = AggregationMonitoringService(service="leverage")

    # 2. Your business logic - pre-aggregate the count
    transactions = fetch_transactions()
    de_mca_count = sum(1 for t in transactions if t.caller == "de" and t.category == "mca")

    # 3. Record ONCE per metric per DAG run
    monitor.recordData(
        metric=LeverageMetrics.TAGGED,
        value=de_mca_count,
        entity_id="de_mca",
    )
```

### Method Signature

```python
monitor.recordData(
    metric: Metric,        # Metric object from registry (e.g., LeverageMetrics.TAGGED)
    value: int | float,    # Pre-aggregated value
    entity_id: str,        # Unique identifier for deduplication
)
```

### Recording Multiple Metrics (Batch)

Use `recordDataBatch` to record multiple metrics at once:

```python
from collections import Counter
from pulse import AggregationMonitoringService
from pulse.registry import LeverageMetrics

def process_transactions(**context):
    monitor = AggregationMonitoringService(service="leverage")

    transactions = fetch_transactions()

    # Pre-aggregate by (caller, category)
    counts = Counter()
    for txn in transactions:
        counts[(txn.caller, txn.category)] += 1

    # Record all combinations in a single batch
    metrics = [
        {"metric": LeverageMetrics.TAGGED, "value": count, "entity_id": f"{caller}_{category}"}
        for (caller, category), count in counts.items()
    ]
    monitor.recordDataBatch(metrics)
```

### What NOT to Do

```python
# ❌ WRONG: Recording inside a loop (one message per transaction)
for txn in transactions:
    monitor.recordData(metric=LeverageMetrics.TAGGED, value=1, entity_id=txn.id)

# ✅ CORRECT: Pre-aggregate, then record once
count = sum(1 for t in transactions if t.caller == "de" and t.category == "mca")
monitor.recordData(metric=LeverageMetrics.TAGGED, value=count, entity_id="de_mca")
```

---

## View Metrics in Grafana

### Table: `monitoring_source_metrics`

| Column | Type | Example |
|--------|------|---------|
| `row_id` | VARCHAR(512) | `leverage_dag_process_scheduled__2026-01-21T14:00:00_tagged_de_mca` |
| `metric_name` | VARCHAR(255) | `tagged` |
| `metric_value` | NUMERIC | `150` |
| `created_at` | TIMESTAMP | `2026-01-21 14:30:00+00` |
| `created_by` | VARCHAR(64) | `leverage_dag` |

### Grafana Query Examples

**Last 24 hours by metric:**

```sql
SELECT
    created_at,
    metric_name,
    metric_value
FROM monitoring_source_metrics
WHERE created_by = 'leverage_dag'
    AND metric_name = 'tagged'
    AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC
```

**Hourly aggregation:**

```sql
SELECT
    DATE_TRUNC('hour', created_at) as hour,
    metric_name,
    SUM(metric_value) as total
FROM monitoring_source_metrics
WHERE metric_name = 'tagged'
    AND created_at > NOW() - INTERVAL '7 days'
GROUP BY hour, metric_name
ORDER BY hour DESC
```

**Filter by entity_id pattern:**

```sql
SELECT * FROM monitoring_source_metrics
WHERE entity_id LIKE 'de_%'
```

---

## Troubleshooting

### Metrics Not Appearing

1. Check Airflow logs for recording:
   ```
   INFO - Recorded metric: tagged = 150
   ```

2. Check consumer DAG:
   - Go to Airflow → DAG: `metrics.source_consumer`
   - Verify last run was successful
   - Check task logs for your queue name

3. Query database directly:
   ```sql
   SELECT COUNT(*) FROM monitoring_source_metrics
   WHERE created_by = 'your_dag_id' AND created_at > NOW() - INTERVAL '1 day';
   ```

### Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Service 'xyz' not registered` | Service not in registry | Add `ServiceSchema` to `METRICS_REGISTRY` in `pulse/registry.py` |
| `Metric 'abc' is not registered for service` | Metric not defined for this service | Add `Metric` to your service's `metrics` tuple |
| `metric must be a Metric object` | Passed string instead of Metric | Use `LeverageMetrics.TAGGED` instead of `"tagged"` |
| `entity_id is required` | Didn't provide entity_id | Add `entity_id` parameter |
| `entity_id cannot be empty` | Empty string passed | Use meaningful identifier |
| `Value must be numeric` | Wrong type | Use `int` or `float` value |

---

## Full Example: Leverage Service

### Files Created

**Registry** (`pulse/registry.py`):

```python
class LeverageMetrics:
    """Metrics for the leverage service."""
    TAGGED = Metric(name="tagged", type=MetricType.COUNTER)
    MATCH_LATENCY_MS = Metric(name="match_latency_ms", type=MetricType.TIMING)

ServiceSchema(
    service="leverage",
    queue_name=PulseQueues.LEVERAGE_METRICS,
    owner=Owners.DATA_SCIENCE,
    metrics=(
        LeverageMetrics.TAGGED,
        LeverageMetrics.MATCH_LATENCY_MS,
    ),
),
```

**EQM Config** (`data_db_utils/entity_queue_manager/queue_managers_configs/pulse_leverage_config.yaml`):

```yaml
QueueManagerConfigurations:
  name: PULSE_LEVERAGE
  queues:
    - PULSE_LEVERAGE_METRICS_QUEUE
  entity_identifier_field: row_id
  max_ttl_time: 2592000
```

### DAG Code

```python
from collections import Counter
from pulse import AggregationMonitoringService
from pulse.registry import LeverageMetrics

def process_leverage(**context):
    monitor = AggregationMonitoringService(service="leverage")

    transactions = fetch_leverage_transactions()

    # Pre-aggregate
    counts = Counter()
    for txn in transactions:
        counts[(txn.caller, txn.category)] += 1

    # Record all in a single batch
    metrics = [
        {"metric": LeverageMetrics.TAGGED, "value": count, "entity_id": f"{caller}_{category}"}
        for (caller, category), count in counts.items()
    ]
    monitor.recordDataBatch(metrics)
```

Example queries for Grafana can be found here: [Example Grafana Queries for Leverage Tagging Requirements](#)

---

## FAQ

**Q: How often should I record?**
A: Once per metric per DAG run. Pre-aggregate in your code.

**Q: What if my DAG retries?**
A: Safe. Same `row_id` is generated from `dag_id + task_id + run_id + metric_name + entity_id`, duplicate insert is silently ignored.

**Q: When do metrics appear in Grafana?**
A: Within 1 day. Consumer DAG (`metrics.aggregate_consumer`) runs once per day.

**Q: Can I add a new metric to existing service?**
A: Yes. Add `Metric` to the `metrics` tuple in `registry.py`, submit PR. No consumer changes needed.

**Q: Can I add new enum values to Owners or PulseQueues?**
A: Yes. Add to the enum in `registry.py`, submit PR.

**Q: What's the max metric name length?**
A: 255 characters. Keep names short.

**Q: What's the max entity_id length?**
A: 512 characters.
