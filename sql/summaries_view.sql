DROP VIEW budget_period_summary;

CREATE VIEW budget_periodsummary AS
SELECT 
    s.id AS scheme_id,
    s.name AS scheme_name,
    p.id AS period_id,
    p.label AS period_label,
    p.end AS period_end,
    t.category_id AS category_id,
    c.full_path as full_path,
    SUM(t.amount) AS amount
FROM 
    budget_periodscheme s
    JOIN budget_period p ON p.scheme_id = s.id
    JOIN budget_transaction t ON t.trn_date BETWEEN p.start_date AND p.end_date
    JOIN budget_category c ON c.id = t.category_id

GROUP BY 
    s.id,
    s.name,
    p.id,
    p.label,
    p.end,
    t.category_id,
    c.full_path
;
