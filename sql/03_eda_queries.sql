-- Exploratory questions. Run them one by one in psql, DBeaver or pgAdmin.

-- 1. How much data was lost in cleaning?
SELECT
    (SELECT COUNT(*) FROM raw_transactions)   AS raw_rows,
    (SELECT COUNT(*) FROM clean_transactions) AS clean_rows,
    (SELECT COUNT(*) FROM raw_transactions WHERE customer_id IS NULL) AS rows_without_customer;

-- 2. Revenue and active customers per month
SELECT
    DATE_TRUNC('month', invoice_date)::date AS month,
    ROUND(SUM(line_total)::numeric, 0)      AS revenue,
    COUNT(DISTINCT customer_id)             AS active_customers,
    COUNT(DISTINCT invoice)                 AS orders
FROM clean_transactions
GROUP BY 1
ORDER BY 1;

-- 3. Top 10 countries by revenue (the UK dominates)
SELECT
    country,
    COUNT(DISTINCT customer_id)        AS customers,
    ROUND(SUM(line_total)::numeric, 0) AS revenue
FROM clean_transactions
GROUP BY country
ORDER BY revenue DESC
LIMIT 10;

-- 4. Top 10 products by units sold
SELECT
    stock_code,
    MAX(description) AS description,
    SUM(quantity)    AS units
FROM clean_transactions
GROUP BY stock_code
ORDER BY units DESC
LIMIT 10;

-- 5. How many orders does a customer usually place? (many buy only once)
WITH orders_per_customer AS (
    SELECT customer_id, COUNT(DISTINCT invoice) AS orders
    FROM clean_transactions
    GROUP BY customer_id
)
SELECT
    orders,
    COUNT(*) AS customers
FROM orders_per_customer
GROUP BY orders
ORDER BY orders
LIMIT 15;

-- 6. Share of invoices that are cancellations
SELECT
    ROUND(100.0 * COUNT(DISTINCT invoice) FILTER (WHERE invoice LIKE 'C%')
          / COUNT(DISTINCT invoice), 2) AS pct_cancelled_invoices
FROM raw_transactions;
