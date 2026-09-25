BEGIN WORK;
\copy budget_budget (due_date,amount,notes,account_id,category_id,type,seq) FROM {1} WITH (FORMAT CSV,HEADER TRUE,DELIMITER ',',QUOTE '"',ESCAPE '"');
COMMIT WORK;