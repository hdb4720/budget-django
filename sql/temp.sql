SELECT s.name AS scheme_name
    , p.start_date AS period_start
    , p.end_date AS period_end
    -- , 
    -- t.category_id,
    -- t.account_id,
    -- c.full_path AS category,
    -- a.short_name AS account,    t.trn_date AS date,
    -- t.amount AS activity,
    -- 0 AS budget
FROM budget_periodscheme s
    JOIN budget_period p ON p.scheme_id = s.id
    -- JOIN budget_transaction t ON t.trn_date BETWEEN p.start_date AND p.end_date
    -- LEFT JOIN budget_category c ON t.category_id = c.id
    -- LEFT JOIN budget_account a ON t.account_id = a.idWHERE s.name LIKE '%{1}%'
    -- AND p.start_date >= '{2}' AND p.end_date <= '{2}'
    -- AND t.trn_date BETWEEN p.start_date AND p.end_date
WHERE s.name LIKE '%{1}%'
AND p.start_date >= '{2}' AND p.end_date <= '{2}'