SELECT 
    c.id,
    c.name,
    c.full_path
FROM 
    budget_category c
ORDER BY 
    c.full_path;
