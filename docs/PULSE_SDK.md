# Pulse SDK Documentation

## Overview
The Pulse SDK allows your Airflow DAGs to emit operational metrics to PostgreSQL (`monitoring_source_metrics` table) for visualization in Grafana.

**Use case:** Track transaction counts, processing metrics, or any numeric values you want to monitor over time.

---

## Setup: Register a New Service

### Step 1: Add Service to Python Registry

File: `pulse/registry.py`

```python
from pulse.registry import (
    METRICS_REGISTRY,
    Metric,
    MetricType,
    Owners,
    PulseQueues,
    ServiceSchema,
)

# Add your queue to PulseQueues enum
class PulseQueues(str, Enum):
    LEVERAGE_METRICS = "PULSE_LEVERAGE_METRICS_QUEUE"
    YOUR_SERVICE_METRICS = "PULSE_YOUR_SERVICE_METRICS_QUEUE"  # Add this

# Add your service to METRICS_REGISTRY
METRICS_REGISTRY: list[ServiceSchema] = [
    ServiceSchema(
        service="leverage",
        queue_name=PulseQueues.LEVERAGE_METRICS,
        owner=Owners.DATA_SCIENCE,
        metrics=(
            Metric(name="tagged", type=MetricType.COUNTER),
            Metric(name="match_latency_ms", type=MetricType.TIMING),
        ),
    ),
    # Add your service here
    ServiceSchema(
        service="your_service",
        queue_name=PulseQueues.YOUR_SERVICE_METRICS,
        owner=Owners.DATA_ENGINEERING,
        metrics=(
            Metric(name="total_tran", type=MetricType.COUNTER),
            Metric(name="processing_time_ms", type=MetricType.TIMING),
        ),
    ),
]
```

**Field Reference:**

| Field | Required | Description |
|-------|----------|-------------|
| `service` | Yes | Service name used in `AggregationMonitoringService(service="...")` |
| `queue_name` | Yes | Queue from `PulseQueues` enum |
| `owner` | Yes | Team from `Owners` enum (e.g., `DATA_SCIENCE`, `DATA_ENGINEERING`) |
| `metrics` | Yes | Tuple of `Metric` definitions |

**Metric Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Metric name (e.g., `"total_tran"`) |
| `type` | No | `MetricType.COUNTER` (default), `GAUGE`, or `TIMING` |
| `description` | No | Human-readable description |

### Step 2: Create EQM Configuration

File: `data_db_utils/entity_queue_manager/queue_managers_configs/{service}_metrics_config.yaml`

```yaml
QueueManagerConfigurations:
  name: PULSE_YOUR_SERVICE
  queues:
    - PULSE_YOUR_SERVICE_METRICS_QUEUE
  entity_identifier_field: row_id
  max_ttl_time: 2592000
```

| Field | Value | Why |
|-------|-------|-----|
| `name` | `PULSE_YOUR_SERVICE` | Manager identifier (prefix of queue name) |
| `queues` | `[PULSE_YOUR_SERVICE_METRICS_QUEUE]` | Must match `queue_name` in registry |
| `entity_identifier_field` | `row_id` | Always use `row_id`. Enables deduplication on DAG retries |
| `max_ttl_time` | `2592000` | 30 days in seconds. Messages expire if not consumed |

### Step 3: Submit PR

Create PR with your changes to the registry and EQM config. After merge, the consumer DAG automatically discovers your queue.

---

## Usage: Emit Metrics in Your DAG

### Basic Pattern

```python
from pulse import AggregationMonitoringService

def process_transactions(**context):
    # Initialize service (Airflow context auto-detected)
    monitor = AggregationMonitoringService(service="leverage")

    # Your business logic
    transactions = fetch_transactions()
    de_mca_count = sum(1 for t in transactions if t.caller == "de" and t.category == "mca")

    # Record metric with a unique entity_id
    monitor.recordData(
        metric_name="tagged",
        value=de_mca_count,
        entity_id="de_mca",  # Unique identifier for this metric instance
    )
```

### Method Signature

```python
monitor.recordData(
    metric_name: str,      # Metric name from registry (e.g., "tagged")
    value: int | float,    # Pre-aggregated value
    entity_id: str,        # Unique identifier for deduplication
)
```

### Recording Multiple Metrics

```python
from collections import Counter
from pulse import AggregationMonitoringService

def process_transactions(**context):
    monitor = AggregationMonitoringService(service="leverage")

    transactions = fetch_transactions()

    # Pre-aggregate by (caller, category)
    counts = Counter()
    for txn in transactions:
        counts[(txn.caller, txn.category)] += 1

    # Record each combination once
    for (caller, category), count in counts.items():
        monitor.recordData(
            metric_name="tagged",
            value=count,
            entity_id=f"{caller}_{category}",  # Unique per combination
        )
```

### Batch Recording

```python
from pulse import AggregationMonitoringService

def process_transactions(**context):
    monitor = AggregationMonitoringService(service="leverage")

    metrics = [
        {"metric_name": "tagged", "value": 100, "entity_id": "de_mca"},
        {"metric_name": "tagged", "value": 50, "entity_id": "mle_factor"},
        {"metric_name": "match_latency_ms", "value": 45.2, "entity_id": "batch_1"},
    ]

    count = monitor.recordDataBatch(metrics)
    print(f"Recorded {count} metrics")
```

### What NOT to Do

```python
# ❌ WRONG: Recording inside a loop without unique entity_id
for txn in transactions:
    monitor.recordData("tagged", value=1, entity_id="same_id")  # Duplicates rejected!

# ✅ CORRECT: Pre-aggregate, then record once per unique entity
count = sum(1 for t in transactions if t.caller == "de" and t.category == "mca")
monitor.recordData("tagged", value=count, entity_id="de_mca")
```

---

## Testing

For unit tests, use `MockQueueAdapter` and provide manual `AirflowContext`:

```python
from pulse import AggregationMonitoringService, AirflowContext, MockQueueAdapter

def test_metrics():
    context = AirflowContext(dag_id="test_dag", task_id="test_task", run_id="test_run")
    adapter = MockQueueAdapter()

    monitor = AggregationMonitoringService(
        service="leverage",
        airflow_context=context,
        queue_adapter=adapter,
    )

    monitor.recordData(metric_name="tagged", value=100, entity_id="test_entity")

    # Verify
    assert len(adapter.messages) == 1
    assert adapter.messages[0].metric_name == "tagged"
    assert adapter.messages[0].value == 100.0
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

---

## Troubleshooting

### Metrics Not Appearing

1. **Check Airflow logs for recording:**
   ```
   INFO - Recorded metric: tagged = 150
   ```

2. **Check consumer DAG:**
   - Go to Airflow → DAG: `metrics.source_consumer`
   - Verify last run was successful
   - Check task logs for your queue name

3. **Query database directly:**
   ```sql
   SELECT COUNT(*) FROM monitoring_source_metrics
   WHERE created_by = 'your_dag_id' AND created_at > NOW() - INTERVAL '1 day';
   ```

### Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Service 'xyz' not registered` | Service not in registry | Add `ServiceSchema` to `METRICS_REGISTRY` in `pulse/registry.py` |
| `Metric 'abc' is not registered` | Metric not defined | Add `Metric` to service's `metrics` tuple |
| `entity_id is required` | Missing entity_id | Provide unique `entity_id` for each metric |
| `entity_id cannot be empty` | Empty string | Use meaningful identifier |
| `Value must be numeric` | Wrong type | Pass `int` or `float` value |

---

## Full Example: Leverage Service

### Registry Configuration

```python
# In pulse/registry.py
ServiceSchema(
    service="leverage",
    queue_name=PulseQueues.LEVERAGE_METRICS,
    owner=Owners.DATA_SCIENCE,
    metrics=(
        Metric(name="tagged", type=MetricType.COUNTER),
        Metric(name="match_latency_ms", type=MetricType.TIMING),
    ),
),
```

### EQM Config

File: `data_db_utils/entity_queue_manager/queue_managers_configs/pulse_leverage_config.yaml`

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

def process_leverage(**context):
    monitor = AggregationMonitoringService(service="leverage")

    transactions = fetch_leverage_transactions()

    # Pre-aggregate
    counts = Counter()
    for txn in transactions:
        counts[(txn.caller, txn.category)] += 1

    # Record
    for (caller, category), count in counts.items():
        monitor.recordData(
            metric_name="tagged",
            value=count,
            entity_id=f"{caller}_{category}",
        )
```

---

## FAQ

**Q: How often should I record?**
A: Once per metric per unique entity_id per DAG run. Pre-aggregate in your code.

**Q: What if my DAG retries?**
A: Safe. Same idempotency key is generated from `dag_id + task_id + run_id + metric_name + entity_id`. Duplicate inserts are silently ignored.

**Q: When do metrics appear in Grafana?**
A: Within 1 day. Consumer DAG (`metrics.aggregate_consumer`) runs once per day.

**Q: Can I add a new metric to existing service?**
A: Yes. Add `Metric` to the service's `metrics` tuple in `registry.py`, submit PR. No consumer changes needed.

**Q: What's the max metric name length?**
A: 255 characters. Keep names short.

**Q: What's the max entity_id length?**
A: 512 characters.

---

## Grafana Query Examples

### 1. Daily Total Processed

```sql
SELECT SUM(metric_value) as total_transactions
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time = CURRENT_DATE - 1;
```

### 2. 7-Day Trend

```sql
SELECT
    aggregation_time::DATE as date,
    SUM(metric_value) as total
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time >= CURRENT_DATE - 7
GROUP BY aggregation_time
ORDER BY aggregation_time;
```

### 3. Week-over-Week Comparison

```sql
SELECT
    'This Week' as period,
    SUM(metric_value) as total
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time >= DATE_TRUNC('week', CURRENT_DATE)
UNION ALL
SELECT
    'Last Week' as period,
    SUM(metric_value) as total
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time >= DATE_TRUNC('week', CURRENT_DATE) - INTERVAL '7 days'
  AND aggregation_time < DATE_TRUNC('week', CURRENT_DATE);
```

### 4. Filter by Entity ID Pattern

```sql
SELECT * FROM monitoring_source_metrics
WHERE entity_id LIKE 'de_%'
  AND created_at > NOW() - INTERVAL '24 hours';
```
