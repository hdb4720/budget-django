SELECT 
    s.name, 
    p.label,
    MIN(t.trn_date), 
    MAX(t.trn_date), 
    SUM(t.amount)
FROM 
budget_periodscheme s,
budget_period p,
budget_transaction t
WHERE s.name = '4th Wednesday'
AND p.scheme_id = s.id
and p.end >= '2026-01-01'
AND t.trn_date BETWEEN p.start AND p.end
GROUP BY
    s.name, 
    p.label
ORDER BY 
    s.name, 
    p.label
;
