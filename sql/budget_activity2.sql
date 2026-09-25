SELECT c.full_path AS category,
    p.end AS date,
    SUM(t.amount) AS activity,
    0 AS budget
FROM budget_periodscheme s
    LEFT JOIN budget_period p ON p.scheme_id = s.id
    LEFT JOIN budget_transaction t ON t.trn_date BETWEEN p.start_date AND p.end_date
    LEFT JOIN budget_category c ON t.category_id = c.id
WHERE s.name LIKE '%{1}%'
    AND p.start_date <= '{2}'
    AND p.end_date >= '{2}'
    AND t.trn_date BETWEEN p.start AND p.end
GROUP BY c.full_path, p.end_date
UNION ALL
SELECT c.full_path AS category,
    b.due_date AS date,
    0 AS activity,
    b.amount AS budget
FROM budget_periodscheme s
    LEFT JOIN budget_period p ON p.scheme_id = s.id
    LEFT JOIN budget_budget b ON b.due_date BETWEEN p.start AND p.end
    LEFT JOIN budget_category c ON b.category_id = c.id
WHERE s.name LIKE '%{1}%'
    AND p.start_date <= '{2}' AND p.end_date >= '{2}'
    AND b.due_date BETWEEN p.start_date AND p.end_date
ORDER BY 1, 2;