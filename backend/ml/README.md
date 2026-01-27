# BizAnalyzer ML - Design Notes

This folder contains high-level configuration and documentation for planned
machine learning pipelines for BizAnalyzer. This is a lightweight, read-only
design artifact — no model training or database queries are performed here.

## ML Goals

- Predict monthly profit per business (forecasting task).
- Predict top-selling items for a given business and month (ranking / item-level
  demand prediction).

## Authoritative Data Sources

- `analytics_monthly` (view): monthly-level aggregates per business. Expected
  columns include `business_id`, `month`, `sales`, `cost`, `profit`.
- `ml_transactions` (view): transaction-level rows prepared for ML. Expected
  columns include `date`, `month`, `business_id`, `inventory_id`, `item_name`,
  `category`, `quantity`, `sales_amount`, `cost_amount`, `profit`.

## Feature definitions (high-level)

- Profit model features (examples):
  - Historical monthly `sales` and `cost` (from `analytics_monthly`)
  - Business identifier (`business_id`) and calendar features (`month`, lagged
    months, seasonality indicators)

- Item-sales model features (examples):
  - Per-transaction/item aggregates such as `quantity`, `sales_amount`,
    `cost_amount`, `category`, `inventory_id`, `item_name`
  - Business and temporal identifiers (`business_id`, `month`, day-of-week,
    month-of-year)

## Target variables

- Monthly profit target: `profit` (from `analytics_monthly`).
- Item sales target: `quantity` (units sold per item per transaction / aggregated
  per-month in `ml_transactions`). Alternative targets include `sales_amount`.

## In scope vs out of scope

In scope:
- Defining features and targets for reproducible ML pipelines.
- Small, dependency-free helpers and configuration constants.

Out of scope for this folder:
- Training models or persisting artifacts.
- Direct database access or ETL logic.
- Adding new runtime dependencies.

## Next steps (for engineering)

1. Implement data extraction and validation jobs that materialize features
   from the authoritative views into a model-ready dataset.
2. Prototype models in an isolated environment using the feature lists below.
3. Add unit/integration tests and CI steps for reproducibility.
