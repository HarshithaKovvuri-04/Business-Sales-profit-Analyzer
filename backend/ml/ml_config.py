"""ML configuration constants for BizAnalyzer.

This module declares the canonical feature and target column names used by
ML pipelines. The lists are intentionally declarative and do not perform any
I/O or imports of database libraries.
"""

# Profit prediction (monthly-level)
# Source: analytics_monthly view (expected columns: business_id, month, sales, cost, profit)
FEATURE_COLUMNS_PROFIT = [
    # identifiers
    'business_id',
    'month',
    # canonical predictors
    'sales',  # numeric: total sales for the month
    'cost',   # numeric: total cost (COGS) for the month
    # downstream pipelines may add lagged features such as sales_lag_1, sales_lag_12, etc.
]

TARGET_COLUMN_PROFIT = 'profit'


# Item-level sales prediction
# Source: ml_transactions view (expected columns: date, month, business_id, inventory_id,
# item_name, category, quantity, sales_amount, cost_amount, profit)
FEATURE_COLUMNS_ITEM_SALES = [
    'business_id',
    'month',
    'inventory_id',
    'item_name',
    'category',
    # numeric features
    'sales_amount',
    'cost_amount',
    # quantity can be used as a feature when predicting revenue or next-period demand
    'quantity',
]

# Predict per-row or aggregated units sold; pipelines may aggregate by (business_id, month, item_name)
TARGET_COLUMN_ITEM_SALES = 'quantity'

__all__ = [
    'FEATURE_COLUMNS_PROFIT', 'TARGET_COLUMN_PROFIT',
    'FEATURE_COLUMNS_ITEM_SALES', 'TARGET_COLUMN_ITEM_SALES'
]
