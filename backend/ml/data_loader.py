"""Data loading utilities for ML datasets.

Provides functions that extract and transform data from the authoritative
analytics views into pandas DataFrames ready for ML modeling.

Functions:
- get_monthly_profit_dataset(db, business_id)
- get_item_sales_dataset(db, business_id)

Notes:
- These functions expect a SQLAlchemy `Session` passed as `db`.
- Pandas is required at runtime; if pandas is not available the functions
  will raise an ImportError with a helpful message.
"""
from typing import Any
from sqlalchemy import text


def _ensure_pandas():
    try:
        import pandas as pd
        return pd
    except Exception as e:
        raise ImportError("pandas is required for ML data transformations; please install pandas") from e


def _to_float(v):
    try:
        if v is None:
            return 0.0
        return float(v)
    except Exception:
        return 0.0


def get_monthly_profit_dataset(db: Any, business_id: int):
    """Return monthly profit dataset as a pandas DataFrame.

    The returned DataFrame columns:
      - month (YYYY-MM string)
      - year (int)
      - month_num (1-12)
      - total_sales (float)
      - total_cost (float)
      - total_profit (float)
      - rolling_3m_sales (float)  # sum over current and previous 2 months
      - rolling_3m_profit (float)

    Empty query results return an empty DataFrame with the above columns.
    """
    pd = _ensure_pandas()

    sql = text("SELECT month, sales, cost, profit FROM analytics_monthly WHERE business_id = :bid ORDER BY month ASC")
    rows = db.execute(sql, {"bid": business_id}).fetchall()

    cols = ['month', 'year', 'month_num', 'total_sales', 'total_cost', 'total_profit', 'rolling_3m_sales', 'rolling_3m_profit']

    if not rows:
        return pd.DataFrame(columns=cols)

    records = []
    for row in rows:
        mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
        month = mapping.get('month')
        sales = _to_float(mapping.get('sales'))
        cost = _to_float(mapping.get('cost'))
        profit = _to_float(mapping.get('profit'))
        records.append({'month': month, 'total_sales': sales, 'total_cost': cost, 'total_profit': profit})

    df = pd.DataFrame.from_records(records)
    # parse month -> timestamp at start of month
    df['month_parsed'] = pd.to_datetime(df['month'].astype(str) + '-01', errors='coerce')
    df['year'] = df['month_parsed'].dt.year
    df['month_num'] = df['month_parsed'].dt.month

    # ensure numeric types
    df['total_sales'] = pd.to_numeric(df['total_sales'], errors='coerce').fillna(0.0)
    df['total_cost'] = pd.to_numeric(df['total_cost'], errors='coerce').fillna(0.0)
    df['total_profit'] = pd.to_numeric(df['total_profit'], errors='coerce').fillna(0.0)

    # rolling sums (window includes current row and previous 2 rows)
    df = df.sort_values('month_parsed').reset_index(drop=True)
    df['rolling_3m_sales'] = df['total_sales'].rolling(window=3, min_periods=1).sum()
    df['rolling_3m_profit'] = df['total_profit'].rolling(window=3, min_periods=1).sum()

    out = df[['month', 'year', 'month_num', 'total_sales', 'total_cost', 'total_profit', 'rolling_3m_sales', 'rolling_3m_profit']].copy()
    return out


def get_item_sales_dataset(db: Any, business_id: int):
    """Return item-level monthly sales dataset as a pandas DataFrame.

    Steps:
      - Query `ml_transactions` for the business
      - Group by (`item_name`, `month`) and aggregate sums
      - Compute `margin = sales_amount - cost_amount`
      - Add `month_num` and per-item `rolling_3m_quantity`

    Returned columns include:
      item_name, month, quantity, sales_amount, cost_amount, profit, margin, month_num, rolling_3m_quantity

    Empty results return an empty DataFrame with the above columns.
    """
    pd = _ensure_pandas()

    sql = text("SELECT item_name, month, COALESCE(quantity,0) AS quantity, COALESCE(sales_amount,0) AS sales_amount, COALESCE(cost_amount,0) AS cost_amount, COALESCE(profit,0) AS profit FROM ml_transactions WHERE business_id = :bid")
    rows = db.execute(sql, {"bid": business_id}).fetchall()

    cols = ['item_name', 'month', 'quantity', 'sales_amount', 'cost_amount', 'profit', 'margin', 'month_num', 'rolling_3m_quantity']

    if not rows:
        return pd.DataFrame(columns=cols)

    records = []
    for row in rows:
        mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
        item = mapping.get('item_name')
        month = mapping.get('month')
        qty = mapping.get('quantity')
        sales_amount = mapping.get('sales_amount')
        cost_amount = mapping.get('cost_amount')
        profit = mapping.get('profit')
        records.append({
            'item_name': item,
            'month': month,
            'quantity': float(qty) if qty is not None else 0.0,
            'sales_amount': _to_float(sales_amount),
            'cost_amount': _to_float(cost_amount),
            'profit': _to_float(profit)
        })

    df = pd.DataFrame.from_records(records)
    # aggregate by item_name + month
    agg = df.groupby(['item_name', 'month'], dropna=False).agg({
        'quantity': 'sum',
        'sales_amount': 'sum',
        'cost_amount': 'sum',
        'profit': 'sum'
    }).reset_index()

    # derived features
    agg['margin'] = agg['sales_amount'] - agg['cost_amount']
    agg['month_parsed'] = pd.to_datetime(agg['month'].astype(str) + '-01', errors='coerce')
    agg['month_num'] = agg['month_parsed'].dt.month

    # rolling 3-month quantity per item
    agg = agg.sort_values(['item_name', 'month_parsed']).reset_index(drop=True)
    def _rolling_qty(g):
        g = g.sort_values('month_parsed')
        g['rolling_3m_quantity'] = g['quantity'].rolling(window=3, min_periods=1).sum()
        return g

    agg = agg.groupby('item_name', group_keys=False).apply(_rolling_qty).reset_index(drop=True)

    out = agg[['item_name', 'month', 'quantity', 'sales_amount', 'cost_amount', 'profit', 'margin', 'month_num', 'rolling_3m_quantity']].copy()
    return out
