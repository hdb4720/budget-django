SELECT now() FROM dual;
SELECT 
    budget_transaction.category_id AS category_id,
    budget_category.full_path AS category__full_path,
    MIN(budget_transaction.amount) AS min_amount,
    MAX(budget_transaction.amount) AS max_amount,
    AVG(budget_transaction.amount) AS avg_amount,
    MAX(budget_transaction.trn_date) AS last_date,
    (SELECT SUM(V0.amount) AS total
    FROM budget_transaction V0
    INNER JOIN budget_category V1 ON (V0.category_id = V1.id)
        WHERE (NOT (V1.full_path::text LIKE '[%' AND V1.full_path IS NOT NULL) 
        AND V0.trn_date <= to_date('2026-09-22','YYYY-MM-DD') 
        AND V0.category_id = (budget_transaction.category_id) 
        AND V0.trn_date = 
        (SELECT U0.trn_date AS trn_date 
        FROM budget_transaction U0 
        INNER JOIN budget_category U1 
            ON (U0.category_id = U1.id) 
            WHERE (NOT (U1.full_path::text LIKE '[%' 
            AND U1.full_path IS NOT NULL) 
        AND U0.trn_date <= to_date('2026-09-22', 'YYYY-MM-DD') 
        AND U0.category_id = (V0.category_id)
    ) 
    ORDER BY 1 DESC LIMIT 1
    )
    ) 
GROUP BY 
    V0.category_id, 
    V0.trn_date) AS last_amt 
            FROM budget_transaction 
            LEFT OUTER JOIN budget_category 
            ON (budget_transaction.category_id = budget_category.id) 
            WHERE (NOT (budget_category.full_path::text LIKE '[%' 
            AND budget_category.full_path IS NOT NULL) 
            AND budget_transaction.trn_date <= to_date('2026-09-22', 'YYYY-MM-DD')
        ) 
        GROUP BY 1, 2, 7 
        ORDER BY 1 ASC
;
SELECT now() FROM dual;