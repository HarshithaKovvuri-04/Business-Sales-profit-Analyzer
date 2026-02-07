from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from .. import crud
from .deps import get_db_dep, get_current_user
import logging

router = APIRouter()


@router.get('/summary/{business_id}')
def summary(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    # staff are not allowed to access financial summaries
    if role == 'staff':
        raise HTTPException(status_code=403, detail='Not authorized')
    # Compute canonical financial totals using explicit sources:
    # - Revenue: sum of Income transactions
    # - Operating Expenses: sum of Expense transactions
    # - COGS: sum of cost_amount from ml_transactions view
    try:
        # Revenue (Income transactions) - use COALESCE in SQL to ensure numeric 0 when no rows
        rev_row = db.execute(text("SELECT COALESCE(SUM(amount),0) AS revenue FROM transactions WHERE business_id = :bid AND type = 'Income'"), {'bid': business_id}).fetchone()
        total_income = float(rev_row._mapping['revenue'] if hasattr(rev_row, '_mapping') else (rev_row[0] if rev_row and len(rev_row) > 0 else 0.0))

        # Operating expenses (Expense transactions)
        exp_row = db.execute(text("SELECT COALESCE(SUM(amount),0) AS expenses FROM transactions WHERE business_id = :bid AND type = 'Expense'"), {'bid': business_id}).fetchone()
        total_expense = float(exp_row._mapping['expenses'] if hasattr(exp_row, '_mapping') else (exp_row[0] if exp_row and len(exp_row) > 0 else 0.0))
        # Log a warning if there are no expense transactions for this business
        cnt_row = db.execute(text("SELECT COUNT(*) AS cnt FROM transactions WHERE business_id = :bid AND type = 'Expense'"), {'bid': business_id}).fetchone()
        expense_count = int(cnt_row._mapping['cnt'] if hasattr(cnt_row, '_mapping') else (cnt_row[0] if cnt_row and len(cnt_row) > 0 else 0))
        if expense_count == 0:
            logging.getLogger(__name__).warning('No expense transactions found for business_id=%s; treating expenses as 0', business_id)

        # COGS from ml_transactions view
        cogs_row = db.execute(text("SELECT COALESCE(SUM(cost_amount),0) AS cogs FROM ml_transactions WHERE business_id = :bid"), {'bid': business_id}).fetchone()
        cogs = float(cogs_row._mapping['cogs'] if hasattr(cogs_row, '_mapping') else (cogs_row[0] if cogs_row and len(cogs_row) > 0 else 0.0))

        # Safe profit calculation: ensure numeric operands
        profit = (total_income or 0.0) - (cogs or 0.0) - (total_expense or 0.0)
        # For display, show total expense as operating_expense + cogs
        display_expense = (total_expense or 0.0) + (cogs or 0.0)
        # Temporary debug print for troubleshooting (can be removed later)
        print({
            'total_income': total_income,
            'operating_expense': total_expense,
            'cogs': cogs,
            'display_expense': display_expense,
            'profit': profit,
        })
        logging.getLogger(__name__).info('analytics.summary values: %s', {'total_income': total_income, 'operating_expense': total_expense, 'cogs': cogs, 'display_expense': display_expense, 'profit': profit})
        return {'total_income': total_income, 'total_expense': display_expense, 'operating_expense': total_expense, 'cogs': cogs, 'profit': profit}
    except Exception:
        logging.exception('Error fetching analytics summary for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while fetching analytics summary')


@router.get('/charts/{business_id}')
def charts(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    # staff are not allowed to access operational/financial charts
    if role == 'staff':
        raise HTTPException(status_code=403, detail='Not authorized')
    logger = logging.getLogger(__name__)
    try:
        income_vs_expense = crud.charts_income_expense_by_date(db, business_id)
        top_selling = crud.top_selling_items(db, business_id)
        category_sales = crud.category_sales(db, business_id)
        # Accountants may see aggregated category sales but must NOT receive item-level top_selling
        if role == 'accountant':
            return {'income_vs_expense': income_vs_expense, 'category_sales': category_sales}
        return {'income_vs_expense': income_vs_expense, 'top_selling': top_selling, 'category_sales': category_sales}
    except Exception as e:
        logger.exception('Error generating charts for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while generating charts')


@router.get('/weekly/{business_id}')
def weekly(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # ensure access via business-specific role
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    # staff are not allowed to access historical analytics
    if role == 'staff':
        raise HTTPException(status_code=403, detail='Not authorized')
    # produce chart-ready structure: { labels: [...], income: [...], expense: [...] }
    raw = crud.analytics_weekly(db, business_id)
    labels = []
    income = []
    expense = []
    for item in raw:
        # prefer ISO date if present, otherwise fall back to label
        d = item.get('date') if isinstance(item, dict) and item.get('date') else item.get('label') if isinstance(item, dict) else None
        labels.append(d)
        income.append(float(item.get('income') or 0))
        expense.append(float(item.get('expense') or 0))
    # ensure arrays lengths match; pad with sensible defaults if not
    maxlen = max(len(labels), len(income), len(expense))
    if len(labels) < maxlen:
        labels.extend([''] * (maxlen - len(labels)))
    if len(income) < maxlen:
        income.extend([0.0] * (maxlen - len(income)))
    if len(expense) < maxlen:
        expense.extend([0.0] * (maxlen - len(expense)))
    logger = logging.getLogger(__name__)
    logger.info('analytics.weekly labels=%s income=%s expense=%s', labels, income, expense)
    return {'labels': labels, 'income': income, 'expense': expense}


@router.get('/monthly/{business_id}')
def monthly(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    if role == 'staff':
        raise HTTPException(status_code=403, detail='Not authorized')
    logger = logging.getLogger(__name__)
    try:
        # Get monthly sales & cogs from analytics_monthly view (sales, cost)
        sql_sales = text("SELECT month, sales, cost FROM analytics_monthly WHERE business_id = :bid ORDER BY month ASC")
        sales_rows = db.execute(sql_sales, {'bid': business_id}).fetchall()
        sales_map = {}
        for row in sales_rows:
            mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
            mon = mapping.get('month')
            if mon is not None and not isinstance(mon, str):
                try:
                    mon = str(mon)
                except Exception:
                    mon = mapping.get('month')
            sales_map[mon] = {'sales': float(mapping.get('sales') or 0.0), 'cogs': float(mapping.get('cost') or 0.0)}

        # Get operating expenses grouped by month from transactions table
        sql_exp = text("SELECT to_char(date_trunc('month', created_at),'YYYY-MM') AS month, COALESCE(SUM(amount),0) AS expenses FROM transactions WHERE business_id = :bid AND type = 'Expense' GROUP BY month ORDER BY month ASC")
        exp_rows = db.execute(sql_exp, {'bid': business_id}).fetchall()
        exp_map = {}
        for row in exp_rows:
            mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
            mon = mapping.get('month')
            exp_map[mon] = float(mapping.get('expenses') or mapping.get('1') or 0.0)

        months = sorted(set(list(sales_map.keys()) + list(exp_map.keys())))
        out = []
        for mon in months:
            sales = sales_map.get(mon, {}).get('sales', 0.0)
            cogs = sales_map.get(mon, {}).get('cogs', 0.0)
            expenses = exp_map.get(mon, 0.0)
            profit = sales - cogs - expenses
            out.append({'month': mon, 'income': float(sales), 'expense': float(expenses), 'cogs': float(cogs), 'profit': float(profit)})
        return out
    except Exception:
        logger.exception('Error fetching monthly analytics for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while fetching monthly analytics')


@router.get('/top-items/{business_id}')
def top_items(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # ensure access via business-specific role
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    # Only owners may receive item-level top items (sensitive)
    if role != 'owner':
        raise HTTPException(status_code=403, detail='Only owner may view top items')
    logger = logging.getLogger(__name__)
    try:
        sql = text("SELECT * FROM analytics_top_items WHERE business_id = :bid")
        rows = db.execute(sql, {'bid': business_id}).fetchall()
        out = []
        for row in rows:
            mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
            rec = {}
            for k, v in mapping.items():
                try:
                    rec[k] = float(v) if hasattr(v, 'as_tuple') or isinstance(v, (int, float)) and not isinstance(v, bool) and not isinstance(v, str) else v
                except Exception:
                    rec[k] = v
            out.append(rec)
        return out
    except Exception:
        logger.exception('Error fetching top items for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while fetching top items')



@router.get('/categories/{business_id}')
def categories(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    # both owner and accountant can view aggregated category sales
    if role == 'staff':
        raise HTTPException(status_code=403, detail='Not authorized')
    return crud.categories_by_business(db, business_id)


@router.get('/expense_categories/{business_id}')
def expense_categories(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    # both owner and accountant can view expense category breakdown
    if role == 'staff':
        raise HTTPException(status_code=403, detail='Not authorized')
    try:
        return crud.expense_categories_by_business(db, business_id)
    except Exception:
        logging.getLogger(__name__).exception('Error fetching expense categories for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while fetching expense categories')


@router.get('/profit/{business_id}')
def profit_trend(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # only owner can request profit trend
    role = crud.get_user_business_role(db, current_user.id, business_id)
    if role is None:
        if not crud.get_business(db, business_id):
            raise HTTPException(status_code=404, detail='Business not found')
        raise HTTPException(status_code=403, detail='Not authorized')
    if role != 'owner':
        raise HTTPException(status_code=403, detail='Only owner may view profit trend')
    # Provide aggregate totals as a safe, numeric response for owners.
    logger = logging.getLogger(__name__)
    try:
        # Revenue from Income transactions
        rev_row = db.execute(text("SELECT COALESCE(SUM(amount),0) AS revenue FROM transactions WHERE business_id = :bid AND type = 'Income'"), {'bid': business_id}).fetchone()
        income = float(rev_row._mapping['revenue'] if hasattr(rev_row, '_mapping') else (rev_row[0] if rev_row and len(rev_row) > 0 else 0.0))
        # Operating expenses from Expense transactions
        exp_row = db.execute(text("SELECT COALESCE(SUM(amount),0) AS expenses FROM transactions WHERE business_id = :bid AND type = 'Expense'"), {'bid': business_id}).fetchone()
        expense = float(exp_row._mapping['expenses'] if hasattr(exp_row, '_mapping') else (exp_row[0] if exp_row and len(exp_row) > 0 else 0.0))
        # COGS from ml_transactions
        cogs_row = db.execute(text("SELECT COALESCE(SUM(cost_amount),0) AS cogs FROM ml_transactions WHERE business_id = :bid"), {'bid': business_id}).fetchone()
        cogs = float(cogs_row._mapping['cogs'] if hasattr(cogs_row, '_mapping') else (cogs_row[0] if cogs_row and len(cogs_row) > 0 else 0.0))
        return {'total_income': income, 'total_expense': expense, 'cogs': cogs, 'profit': income - cogs - expense}
    except Exception:
        logger.exception('Error computing profit totals for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while computing profit')


@router.get('/profit_trend/{business_id}')
def profit_trend_series(business_id: int, db: Session = Depends(get_db_dep), current_user=Depends(get_current_user)):
    # Return per-month profit series for plotting; kept separate to avoid
    # changing the totals contract used by other integrations.
    logger = logging.getLogger(__name__)
    try:
        # Build profit series using:
        # revenue (income transactions per month), cogs (ml_transactions cost_amount per month),
        # and operating expenses (transactions type Expense per month).
        # Query ml_transactions for monthly sales/cost
        sql_ml = text("SELECT month, COALESCE(SUM(sales_amount),0) AS sales, COALESCE(SUM(cost_amount),0) AS cost FROM ml_transactions WHERE business_id = :bid GROUP BY month ORDER BY month ASC")
        ml_rows = db.execute(sql_ml, {'bid': business_id}).fetchall()
        # Build a mapping month -> {sales, cost}
        ml_map = {}
        for row in ml_rows:
            mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
            mon = mapping.get('month') or mapping.get(0)
            ml_map[mon] = {'sales': float(mapping.get('sales') or 0.0), 'cost': float(mapping.get('cost') or 0.0)}

        # Query expenses grouped by month from transactions (operating expenses)
        sql_exp = text("SELECT to_char(date_trunc('month', created_at),'YYYY-MM') AS month, COALESCE(SUM(amount),0) AS expenses FROM transactions WHERE business_id = :bid AND type = 'Expense' GROUP BY month ORDER BY month ASC")
        exp_rows = db.execute(sql_exp, {'bid': business_id}).fetchall()
        exp_map = {}
        for row in exp_rows:
            mapping = row._mapping if hasattr(row, '_mapping') else dict(row)
            mon = mapping.get('month') or mapping.get(0)
            exp_map[mon] = float(mapping.get('expenses') or mapping.get('1') or 0.0)

        # Merge months present in either source
        months = sorted(set(list(ml_map.keys()) + list(exp_map.keys())))
        out = []
        for mon in months:
            revenue = ml_map.get(mon, {}).get('sales', 0.0)
            cogs = ml_map.get(mon, {}).get('cost', 0.0)
            expenses = exp_map.get(mon, 0.0)
            profit = revenue - cogs - expenses
            out.append({'month': mon, 'profit': float(profit)})
        return out
    except Exception:
        logger.exception('Error computing profit trend for business_id=%s', business_id)
        raise HTTPException(status_code=500, detail='Internal server error while computing profit trend')
