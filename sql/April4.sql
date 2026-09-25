SELECT
    a.short_name AS account,
    c.full_path AS category,
    t.trn_date AS date,
    t.description AS description,
    t.amount AS amount
FROM budget_transaction t
LEFT JOIN budget_category c ON t.category_id = c.id
LEFT JOIN budget_account a ON t.account_id = a.id
WHERE (a.name LIKE '%April%' AND c.full_path NOT LIKE '[April%')
OR (a.name NOT LIKE '%[April%' and c.full_path LIKE '%April%')
ORDER BY
    category,
    date, 
    amount