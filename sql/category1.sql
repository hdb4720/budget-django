SELECT ba.short_name AS account,
    bc.full_path AS category,
    bt.trn_date AS trn_date,
    bt.amount AS amount
FROM budget_account ba
    LEFT JOIN budget_transaction bt ON bt.account_id = ba.id
    LEFT JOIN budget_category bc ON bt.category_id = bc.id
WHERE b.short_name LIKE '%{1}%'
    AND bt.trn_date BETWEEN to_date('{2}', 'MMDDYY') AND to_date('{3}', 'MMDDYY')
ORDER BY 
    bc.full_path,
    bt.trn_date;