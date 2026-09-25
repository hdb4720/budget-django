SELECT
FROM budget_period p
LEFT JOIN budget_budget b ON b.due_date BETWEEN p.start AND p.end
LEFT JOIN budget_category c ON c.id = b.category_id
WHERE p.id = {1}
AND c.id = {2}