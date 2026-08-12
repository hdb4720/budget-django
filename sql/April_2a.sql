SELECT
s.name AS scheme,
p.label AS period,
a.name AS account,
c.full_path AS category,
t.trn_date,
t.description,
t.seq,
t.amount
FROM 
budget_periodscheme s,
budget_period p,
budget_transaction t,
budget_account a,
budget_category c
WHERE
s.name = '4th Wednesday' AND
p.scheme_id = s.id AND
t.trn_date BETWEEN p.start AND p.end AND
a.id = t.account_id AND
c.id = t.category_id
AND (
    (a.name LIKE 'April%' AND c.full_path NOT LIKE '[April%' AND c.full_path NOT LIKE 'April%') OR
    (a.name NOT LIKE 'April%' AND (c.full_path LIKE '[April%' OR c.full_path LIKE 'April%'))
)
ORDER BY 1, 2, 3, 4, 5, 6, 7
