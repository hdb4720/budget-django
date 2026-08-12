SELECT 
    ba.short_name AS account,
    bc.full_path AS category,
    SUM(bt.amount) AS amount
FROM 
    budget_account ba
    LEFT JOIN budget_transaction bt ON bt.account_id = ba.id
    LEFT JOIN budget_category bc ON bt.category_id = bc.id
WHERE ba.short_name = '{1}'
  AND bt.trn_date BETWEEN to_date('{2}', 'MMDDYY') 
                      AND to_date('{3}', 'MMDDYY')
GROUP BY 
    ba.short_name,
    bc.full_path
ORDER BY bc.full_path