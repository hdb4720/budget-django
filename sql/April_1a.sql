SELECT
a.name AS account,
c.full_path AS category,
t.trn_date,
SUM(t.amount) AS amount
FROM 
budget_transaction t,
budget_account a,
budget_category c
WHERE
a.id = t.account_id AND
c.id = t.category_id
AND (
    a.name LIKE 'April%' AND c.full_path NOT LIKE '%April%' OR
    a.name NOT LIKE 'April%' AND c.full_path LIKE '%April%'
)
GROUP BY 1, 2, 3
ORDER BY 3, 1, 2
