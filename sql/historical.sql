-- SELECT 
--     c.full_path AS category,
--     MIN(t.amount) AS min_amount,
--     MAX(t.amount) AS max_amount,
--     AVG(t.amount) AS avg_amount
-- FROM 
--     budget_transaction t
--     LEFT JOIN budget_category c ON t.category_id = c.id
-- WHERE t.trn_date < to_date('{1}', 'MMDDYY')
-- GROUP BY 
--     c.full_path
-- ORDER BY 
--     c.full_path;

SELECT c.full_path AS category,
    MIN(ta.amount) AS min_amount,
    MAX(ta.amount) AS max_amount,
    AVG(ta.amount) AS avg_amount
FROM
    budget_category c
    (SELECT p.end, SUM(t.amount) AS amount
    FROM 
        budget_periodscheme s,
        budget_period p,
        budget_transaction t
    WHERE s.name="4th Wednesday" AND p.scheme_id = s.id 
    ANd t.category_id = c.id
    AND t.trn_date BETWEEN p.start AND p.end
    ) ta
GROUP BY 1 order 1;
