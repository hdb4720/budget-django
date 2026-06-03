SELECT MIN(t.tx_date), MAX(t.tx_date), SUM(t.amount)
FROM transactions t
WHERE t.tx_date BETWEEN '2026-05-27' AND '2027-12-31'
