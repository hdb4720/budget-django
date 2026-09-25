SELECT 
    s.name AS scheme,
    p.label AS period,
    MIN(t.trn_date) AS min,
    MAX(t.trn_date) AS min,
    SUM(t.amount) AS sum
FROM budget_periodscheme s,
    budget_period p,
    budget_transaction t
    LEFT JOIN budget_account a ON t.account_id = a.id
    LEFT JOIN budget_category c ON t.category_id = c.id
WHERE s.name LIKE '%{1}%'
    AND p.scheme_id = s.id
    AND p.end >= '{2}'
AND t.trn_date BETWEEN p.start_date AND p.end_date
GROUP BY
    s.name,
    p.label
ORDER BY 
    s.name,
    p.label;