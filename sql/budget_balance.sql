SELECT
    a.name,
    a.opening_balance,
    SUM(t.amount) transactions,
	a.opening_balance + sum(t.amount) balance
FROM
    budget_account a,
    budget_transaction t
WHERE t.account_id = a.id
GROUP BY 
    a.name,
    a.opening_balance
ORDER BY 
    a.name;

