SELECT
    b.due_date,
    b.amount,
    b.account_id,
    b.category_id,
    b.type
FROM budget_budget b
JOIN budget_category c ON c.id = b.category_id
WHERE c.full_path LIKE '%{1}%'
ORDER BY b.due_date