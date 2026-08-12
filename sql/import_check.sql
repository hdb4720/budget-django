\set QUIET on 
\pset pager off 
\pset footer off

\pset tuples_only on
SELECT now() AS ts \gset 
\pset tuples_only off 
\echo 'Report generated at: ' :ts

\connect budgetdb
\echo \echo '=== Django Budget Check ===' \echo

CREATE TEMP TABLE xDjango AS 
SELECT 
    a.name AS nm,
    a.opening_balance + SUM(t.amount) AS bl
FROM 
    budget_account a,
    budget_transaction t
WHERE t.account_id = a.id
GROUP BY 
    a.name,
    a.opening_balance;  

SELECT 
    nm AS account,
    bl AS balance FROM 
    (
        SELECT nm, bl, '0' _ FROM xDjango
        UNION ALL
        SELECT 'Total' nm, sum(bl), '1' _ from xDjango
    )
ORDER BY _, nm;

SELECT s.name,
    p.label,
    MIN(t.trn_date),
    MAX(t.trn_date),
    SUM(t.amount)
FROM budget_periodscheme s,
    budget_period p,
    budget_transaction t
WHERE s.name = '4th Wednesday'
    AND p.scheme_id = s.id
    and p.
end >= '2026-01-01'
AND t.trn_date BETWEEN p.start AND p.
end
GROUP BY s.name,
    p.label
ORDER BY s.name,
    p.label;

\echo ''

\connect budget_import
\echo \echo '=== Excel Budget Check ===' \echo

CREATE TEMP TABLE xExcel AS
SELECT 
    a.name AS nm,
    a.beginning_balance + SUM(t.amount) AS bl
FROM 
    accounts a,
    transactions t
WHERE t.account_id = a.id
GROUP BY 
    a.name,
    a.beginning_balance;

SELECT 
    nm AS account,
    bl AS balance
FROM (
        SELECT nm, bl, '0' _ FROM xExcel
        UNION ALL
        SELECT 'Total' nm, sum(bl), '1' _ from xExcel
    )
ORDER BY  _, nm;

SELECT p.period,
    MIN(t.tx_date),
    MAX(t.tx_date),
    SUM(t.amount)
FROM 
    periods p,
    transactions t
WHERE p.end >= '2026-01-01'
AND t.tx_date BETWEEN p.start AND p.end
GROUP BY p.period
ORDER BY p.period;

