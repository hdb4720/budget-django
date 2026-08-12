SELECT bs.name AS period_scheme,
    bp.label AS period_label,
    ba.short_name AS account,
    bc.full_path AS category,
    bt.trn_date AS trn_date,
    bt.amount AS amount
FROM budget_periodscheme bs
    JOIN budget_period bp ON bp.scheme_id = bs.id
    JOIN budget_transaction bt ON bt.trn_date BETWEEN bp.start AND bp.
end
JOIN budget_category bc ON bt.category_id = bc.id
JOIN budget_account ba ON bt.account_id = ba.id
WHERE LOWER(bs.name) ILIKE '%{1}%'
    AND bp.label = '{2}'
    AND LOWER(bc.full_path) ILIKE '%{3}%'
ORDER BY bc.full_path,
    ba.short_name,
    bt.trn_date;