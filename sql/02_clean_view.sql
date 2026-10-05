-- Purchases we can attribute to a customer. Everything downstream reads from here.
CREATE OR REPLACE VIEW clean_transactions AS
SELECT
    invoice,
    stock_code,
    description,
    quantity,
    invoice_date,
    price,
    quantity * price AS line_total,
    customer_id,
    country
FROM raw_transactions
WHERE customer_id IS NOT NULL
  AND invoice NOT LIKE 'C%'          -- 'C' invoices are cancellations
  AND quantity > 0
  AND price > 0
  -- Postage, fees, discounts and manual adjustments are not products
  AND stock_code NOT IN ('POST', 'DOT', 'M', 'm', 'C2', 'D', 'S', 'B', 'PADS',
                         'CRUK', 'BANK CHARGES', 'ADJUST', 'AMAZONFEE', 'TEST001');

-- Cancelled lines, kept apart because "how often a customer returns things"
-- is a useful signal for churn.
CREATE OR REPLACE VIEW cancellations AS
SELECT
    invoice,
    stock_code,
    quantity,
    invoice_date,
    price,
    customer_id
FROM raw_transactions
WHERE customer_id IS NOT NULL
  AND invoice LIKE 'C%';
