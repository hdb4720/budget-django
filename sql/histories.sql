SELECT now() FROM dual;

SELECT 
    t.category_id AS category_id,
    c.full_path AS full_path,
    MIN(t.amount) AS min,
    MAX(t.amount) AS max,
    AVG(t.amount) AS avg,
    MAX(t.trn_date) AS last_date,
    (
        SELECT SUM(t1.amount) AS last_amt
        FROM budget_transaction t1
        WHERE t1.category_id = t.category_id
        AND t1.trn_date = 
        (SELECT MAX(t2.trn_date) FROM budget_transaction t2
        WHERE t2.category_id = t1.category_id
        AND t2.trn_date <= to_date('{1}', 'MMDDYY')
        )
    ) AS last_amt
FROM budget_transaction t
    LEFT JOIN budget_category c ON t.category_id = c.id
WHERE t.trn_date <= to_date('{1}', 'MMDDYY')
GROUP BY 
    t.category_id,
    c.full_path
;

SELECT now() FROM dual;

