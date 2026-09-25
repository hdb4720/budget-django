SELECT
    c.full_path AS category,
    b.due_date AS due_date,
    b.amount AS amount
FROM budget_budget b
LEFT JOIN budget_category c ON c.id = b.category_id
WHERE c.full_path LIKE '%{1}%'
ORDER BY b.due_date ASC;
