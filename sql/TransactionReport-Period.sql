SELECT
    a.name AS account_name,
    t.description AS description,
    t.memo AS memo,
    t.trn_date AS date,
    c.full_path AS category,
    t.amount AS amount,
    '' AS num
FROM
    budget_periodscheme s,
    budget_period p,
    budget_transaction t
    LEFT JOIN budget_account a ON t.account_id = a.id
    LEFT JOIN budget_category c ON t.category_id = c.id
WHERE
    s.name LIKE '%{1}%' AND
    p.scheme_id = s.id AND
    p.start <='{2}' AND
    p.end >= '{2}' AND
    t.trn_date BETWEEN p.start AND p.end 
ORDER BY
    t.trn_date,
    c.full_path;
