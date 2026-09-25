BEGIN WORK;

SELECT s.name AS scheme,
    p.label AS period,
    b.due_date AS due_date,
    c.full_path AS category,
    b.amount AS amount
FROM budget_periodscheme s,
    budget_period p,
    budget_budget b,
    budget_category c
WHERE s.name LIKE '%{1}%'
    AND p.scheme_id = s.id
    AND p.start_date <= '{2}'
    AND p.end_date >= '{2}'
    AND c.id = b.category_id
    AND b.due_date >= p.start_date
ORDER BY s.name,
    p.label,
    b.due_date,
    c.full_path;

DELETE FROM budget_budget WHERE id IN (
    SELECT b.id
    FROM 
        budget_periodscheme s,
        budget_period p,
        budget_budget b
    WHERE
        s.name LIKE '%{1}%' AND
        p.scheme_id = s.id AND
        p.start_date <= '{2}' AND
        p.end_date >= '{2}' AND
        b.due_date >= p.start_date
);

\copy budget_budget (due_date,amount,notes,account_id,category_id,type,seq) FROM {3} WITH (FORMAT CSV, HEADER TRUE, DELIMITER ',', QUOTE '"', ESCAPE '"');  

SELECT  
    s.name AS scheme,
    p.label AS period,
    b.due_date AS due_date,
    c.full_path AS category,
    b.amount AS amount
FROM budget_periodscheme s,
    budget_period p,
    budget_budget b,
    budget_category c
WHERE s.name LIKE '%{1}%'
    AND p.scheme_id = s.id
    AND p.start_date <= '{2}'
    AND p.end_date >= '{2}'
    AND b.due_date >= p.start_date
    AND c.id = b.category_id
ORDER BY s.name, p.label, b.due_date, c.full_path;

COMMIT WORK;
