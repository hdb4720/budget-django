SELECT 
    s.name AS scheme,
    p.label AS period,
    c.full_path AS category,
    MIN(t.trn_date) AS min,
    MAX(t.trn_date) AS min,
    SUM(t.amount) AS sum
FROM budget_periodscheme s,
    budget_period p,
    budget_transaction t
    LEFT JOIN budget_account a ON t.account_id = a.id
    LEFT JOIN budget_category c ON t.category_id = c.id
WHERE 
    s.name LIKE '%{1}%' AND 
    p.scheme_id = s.id AND
    p.start <= '{2}' AND 
    p.end >= '{2}' AND
    t.trn_date BETWEEN p.start AND p.end
GROUP BY 
    s.name,
    p.label,
    c.full_path
ORDER BY 
    s.name,
    p.label,
    c.full_path;