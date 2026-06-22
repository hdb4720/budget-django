SELECT 
t.*,
a.name AS account,
c.full_path AS category,
p.label AS period
FROM
budget_transaction t,
budget_account a,
budget_category c,
budget_period p,
budget_periodscheme s
WHERE
t.account_id = a.id AND
t.category_id = c.id AND
t.date BETWEEN p.start AND p.end AND
s.id = p.scheme_id AND
s.name = '4th Wednesday';