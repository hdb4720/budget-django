SELECT s.name AS "Scheme",
    p.label AS "Period",
    a.name AS "Account",
    c.full_path AS "Category",
    t.trn_date AS "Date",
    SUM(t.amount) AS "Amount"
FROM budget_transaction t
    LEFT JOIN budget_period p ON t.trn_date BETWEEN p.start AND p.
end
LEFT JOIN budget_periodscheme s ON p.scheme_id = s.id
LEFT JOIN budget_account a ON t.account_id = a.id
LEFT JOIN budget_category c ON t.category_id = c.id
WHERE p.label = '{2}'
    AND s.name like '%{1}%'
    AND(
        (
            a.name LIKE 'April%'
            AND (
                c.full_path NOT LIKE 'April%'
                AND c.full_path NOT LIKE '[April%'
            )
        )
        OR (
            a.name NOT LIKE 'April%'
            AND (
                c.full_path LIKE 'April%'
                OR c.full_path LIKE '[April%'
            )
        )
    )
GROUP BY 
    s.name,
    p.label,
    a.name,
    c.full_path,
    t.trn_date
ORDER BY 1, 2, 3, 4;

-- SELECT s.name AS "Scheme",
--     p.label AS "Period",
--     a.name AS "Account",
--     c.full_path AS "Category",
--     SUM(t.amount) AS "Amount"
-- FROM budget_transaction t
--     LEFT JOIN budget_period p ON t.trn_date BETWEEN p.start AND p.
-- end
-- LEFT JOIN budget_periodscheme s ON p.scheme_id = s.id
-- LEFT JOIN budget_account a ON t.account_id = a.id
-- LEFT JOIN budget_category c ON t.category_id = c.id
-- WHERE p.label = '{2}'
--     AND s.name like '%{1}%'
--     AND(
--         (
--             a.name LIKE 'April%'
--             AND (
--                 c.full_path NOT LIKE 'April%'
--                 AND c.full_path NOT LIKE '[April%'
--             )
--         )
--         OR (
--             a.name NOT LIKE 'April%'
--             AND (
--                 c.full_path LIKE 'April%'
--                 OR c.full_path LIKE '[April%'
--             )
--         )
--     )
-- GROUP BY s.name,
--     p.label,
--     a.name,
--     c.full_path
-- ORDER BY 1, 2, 3;
    
-- SELECT s.name AS "Scheme",
--     p.label AS "Period",
--     a.name AS "Account",
--     SUM(t.amount) AS "Amount"
-- FROM budget_transaction t
--     LEFT JOIN budget_period p ON t.trn_date BETWEEN p.start AND p.
-- end
-- LEFT JOIN budget_periodscheme s ON p.scheme_id = s.id
-- LEFT JOIN budget_account a ON t.account_id = a.id
-- LEFT JOIN budget_category c ON t.category_id = c.id
-- WHERE p.label = '{2}'
--     AND s.name like '%{1}%'
--     AND(
--         (
--             a.name LIKE 'April%'
--             AND (
--                 c.full_path NOT LIKE 'April%'
--                 AND c.full_path NOT LIKE '[April%'
--             )
--         )
--         OR (
--             a.name NOT LIKE 'April%'
--             AND (
--                 c.full_path LIKE 'April%'
--                 OR c.full_path LIKE '[April%'
--             )
--         )
--     )
-- GROUP BY s.name,
--     p.label,
--     a.name
-- ORDER BY 1, 2, 3;

-- SELECT s.name AS "Scheme",
--     p.label AS "Period",
--     SUM(t.amount) AS "Amount"
-- FROM budget_transaction t
--     LEFT JOIN budget_period p ON t.trn_date BETWEEN p.start AND p.
-- end
-- LEFT JOIN budget_periodscheme s ON p.scheme_id = s.id
-- LEFT JOIN budget_account a ON t.account_id = a.id
-- LEFT JOIN budget_category c ON t.category_id = c.id
-- WHERE p.label = '{2}'
--     AND s.name like '%{1}%'
--     AND(
--         (
--             a.name LIKE 'April%'
--             AND (
--                 c.full_path NOT LIKE 'April%'
--                 AND c.full_path NOT LIKE '[April%'
--             )
--         )
--         OR (
--             a.name NOT LIKE 'April%'
--             AND (
--                 c.full_path LIKE 'April%'
--                 OR c.full_path LIKE '[April%'
--             )
--         )
--     )
-- GROUP BY s.name,
--     p.label
-- ORDER BY 1, 2, 3;