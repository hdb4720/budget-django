SELECT MIN(t.date), MAX(t.date), SUM(t.amount)
FROM budget_transaction t
WHERE t.date BETWEEN '2026-05-27' AND '2027-12-31'
