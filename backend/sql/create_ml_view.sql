-- Create ML-ready derived view for sales (do NOT modify core tables)
-- View: ml_transactions
-- Columns:
-- date (date), month (YYYY-MM), business_id, inventory_id, item_name, category,
-- quantity, sales_amount, cost_amount, profit

CREATE OR REPLACE VIEW ml_transactions AS
SELECT
  (date_trunc('day', t.created_at))::date AS date,
  to_char(date_trunc('month', t.created_at), 'YYYY-MM') AS month,
  t.business_id::integer AS business_id,
  t.inventory_id::integer AS inventory_id,
  i.item_name::text AS item_name,
  i.category::text AS category,
  COALESCE(t.used_quantity, 1)::integer AS quantity,
  COALESCE(t.amount, 0)::numeric AS sales_amount,
  (COALESCE(t.used_quantity, 1) * COALESCE(i.cost_price, 0))::numeric AS cost_amount,
  (COALESCE(t.amount, 0) - (COALESCE(t.used_quantity, 1) * COALESCE(i.cost_price, 0)))::numeric AS profit
FROM transactions t
JOIN inventory i ON t.inventory_id = i.id
WHERE t.type = 'Income' AND t.inventory_id IS NOT NULL
ORDER BY date ASC;

-- Validation queries (run in psql):
-- 1) Total sales (sum of sales_amount)
-- SELECT SUM(sales_amount) FROM ml_transactions;
-- 2) Total cost
-- SELECT SUM(cost_amount) FROM ml_transactions;
-- 3) Total profit
-- SELECT SUM(profit) FROM ml_transactions;
-- 4) Monthly profit trend
-- SELECT month, SUM(profit) AS month_profit FROM ml_transactions GROUP BY month ORDER BY month ASC;
-- 5) Top-selling items (by quantity)
-- SELECT item_name, SUM(quantity) AS total_qty, SUM(sales_amount) AS total_sales FROM ml_transactions GROUP BY item_name ORDER BY total_qty DESC LIMIT 20;
