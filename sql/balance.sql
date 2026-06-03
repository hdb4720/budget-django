SELECT
    a.name,
    a.beginning_balance,
    SUM(t.amount) transactions,
	a.beginning_balance + sum(t.amount) balance
FROM
    accounts a,
    transactions t
WHERE t.account_id = a.id
GROUP BY 
    a.name,
    a.beginning_balance
ORDER BY 
    a.name;

