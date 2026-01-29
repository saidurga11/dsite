# Example Grafana Queries for Leverage Tagging Requirements

## 1. Daily Total Processed

**Requirement:** How many transactions did we process today/yesterday?

```sql
-- Total transactions yesterday
SELECT SUM(metric_value) as total_transactions
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time = CURRENT_DATE - 1;
```

## 2. Breakdown by Entity ID Pattern

**Requirement:** How many transactions per caller?

```sql
-- Transactions by caller (using entity_id pattern) yesterday
SELECT
    SPLIT_PART(entity_id, '_', 1) as caller,
    SUM(metric_value) as total
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time = CURRENT_DATE - 1
GROUP BY SPLIT_PART(entity_id, '_', 1)
ORDER BY total DESC;
```

**Result:**
```
| caller | total  |
|--------|--------|
| de     | 12000  |
| mle    | 5000   |
| risk   | 3000   |
```

## 3. Breakdown by Category

**Requirement:** How many transactions per category?

```sql
-- Transactions by category yesterday
SELECT
    SPLIT_PART(entity_id, '_', 2) as category,
    SUM(metric_value) as total
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time = CURRENT_DATE - 1
GROUP BY SPLIT_PART(entity_id, '_', 2)
ORDER BY total DESC;
```

**Result:**
```
| category | total  |
|----------|--------|
| mca      | 10000  |
| factor   | 6000   |
| 0        | 3000   |
| 999999   | 1000   |
```

## 4. Leverage Rate

**Requirement:** What percentage are MCA + Factor vs total?

```sql
-- Leverage rate yesterday
SELECT
    ROUND(
        SUM(CASE WHEN SPLIT_PART(entity_id, '_', 2) IN ('mca', 'factor', 'factor_mca', 'factor_abl')
            THEN metric_value ELSE 0 END) * 100.0
        / NULLIF(SUM(metric_value), 0),
    2) as leverage_rate_pct
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time = CURRENT_DATE - 1;
```

**Result:**
```
| leverage_rate_pct |
|-------------------|
| 80.00             |
```

## 5. Caller + Category Matrix

**Requirement:** Full breakdown by caller AND category

```sql
-- Full breakdown yesterday
SELECT
    SPLIT_PART(entity_id, '_', 1) as caller,
    SPLIT_PART(entity_id, '_', 2) as category,
    metric_value as total
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time = CURRENT_DATE - 1
ORDER BY caller, category;
```

**Result:**
```
| caller | category | total |
|--------|----------|-------|
| de     | mca      | 5000  |
| de     | factor   | 3000  |
| de     | 0        | 2000  |
| mle    | mca      | 3000  |
| mle    | factor   | 1500  |
```

## 6. 7-Day Trend (Total)

**Requirement:** Daily totals for last 7 days

```sql
-- 7-day trend
SELECT
    aggregation_time::DATE as date,
    SUM(metric_value) as total
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time >= CURRENT_DATE - 7
GROUP BY aggregation_time
ORDER BY aggregation_time;
```

**Result:**
```
| date       | total  |
|------------|--------|
| 2026-01-02 | 18000  |
| 2026-01-03 | 19500  |
| 2026-01-04 | 17000  |
| 2026-01-05 | 20000  |
| 2026-01-06 | 21000  |
| 2026-01-07 | 19000  |
| 2026-01-08 | 20000  |
```

## 7. 14-Day Trend by Caller

**Requirement:** Daily totals per caller for last 14 days

```sql
-- 14-day trend by caller
SELECT
    aggregation_time::DATE as date,
    SPLIT_PART(entity_id, '_', 1) as caller,
    SUM(metric_value) as total
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time >= CURRENT_DATE - 14
GROUP BY aggregation_time, SPLIT_PART(entity_id, '_', 1)
ORDER BY aggregation_time, caller;
```

## 8. 14-Day Trend by Category

**Requirement:** Daily totals per category for last 14 days

```sql
-- 14-day trend by category
SELECT
    aggregation_time::DATE as date,
    SPLIT_PART(entity_id, '_', 2) as category,
    SUM(metric_value) as total
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time >= CURRENT_DATE - 14
GROUP BY aggregation_time, SPLIT_PART(entity_id, '_', 2)
ORDER BY aggregation_time, category;
```

## 9. Week-over-Week Comparison

**Requirement:** Compare this week vs last week

```sql
-- Week-over-week comparison
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

## 10. Error Count

**Requirement:** How many errors yesterday?

```sql
-- Errors yesterday
SELECT metric_value as error_count
FROM monitoring_aggregated_metrics
WHERE metric_name = 'error_count'
  AND aggregation_time = CURRENT_DATE - 1;
```

## 11. Error Rate

**Requirement:** Errors as percentage of total

```sql
-- Error rate yesterday
SELECT
    ROUND(
        e.metric_value * 100.0 / NULLIF(t.total, 0),
    2) as error_rate_pct
FROM monitoring_aggregated_metrics e
JOIN (
    SELECT SUM(metric_value) as total
    FROM monitoring_aggregated_metrics
    WHERE metric_name = 'tagged'
      AND aggregation_time = CURRENT_DATE - 1
) t ON true
WHERE e.metric_name = 'error_count'
  AND e.aggregation_time = CURRENT_DATE - 1;
```

## 12. Top Categories by Volume

**Requirement:** Which categories have most volume?

```sql
-- Top 5 categories yesterday
SELECT
    SPLIT_PART(entity_id, '_', 2) as category,
    SUM(metric_value) as total
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time = CURRENT_DATE - 1
GROUP BY SPLIT_PART(entity_id, '_', 2)
ORDER BY total DESC
LIMIT 5;
```

## 13. Daily Leverage Rate Trend

**Requirement:** Leverage rate trend over 14 days

```sql
-- Leverage rate trend
SELECT
    aggregation_time::DATE as date,
    ROUND(
        SUM(CASE WHEN SPLIT_PART(entity_id, '_', 2) IN ('mca', 'factor', 'factor_mca', 'factor_abl')
            THEN metric_value ELSE 0 END) * 100.0
        / NULLIF(SUM(metric_value), 0),
    2) as leverage_rate_pct
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time >= CURRENT_DATE - 14
GROUP BY aggregation_time
ORDER BY aggregation_time;
```

## 14. Filter by Specific Entity ID

**Requirement:** Get metrics for specific caller/category combination

```sql
-- Get all DE MCA metrics
SELECT *
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND entity_id = 'de_mca'
  AND aggregation_time >= CURRENT_DATE - 7
ORDER BY aggregation_time DESC;
```

## 15. List All Unique Entity IDs

**Requirement:** See all recorded entity_id values

```sql
-- List all unique entity_ids for a metric
SELECT DISTINCT entity_id
FROM monitoring_aggregated_metrics
WHERE metric_name = 'tagged'
  AND aggregation_time >= CURRENT_DATE - 7
ORDER BY entity_id;
```
