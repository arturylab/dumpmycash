SELECT * FROM users;
SELECT * FROM accounts;
SELECT * FROM categories;
SELECT * FROM transactions;
SELECT * FROM transfers;

DELETE FROM transactions WHERE user_id = 1;
DELETE FROM accounts WHERE user_id = 1;
DELETE FROM categories WHERE user_id = 1;
DELETE FROM transfers WHERE user_id = 1;

DELETE FROM accounts WHERE user_id <> 1;
DELETE FROM categories WHERE user_id <> 1;
DELETE FROM transactions WHERE user_id <> 1;
DELETE FROM transfers WHERE user_id <> 1;
DELETE FROM users WHERE id <> 1;

TRUNCATE TABLE transfers RESTART IDENTITY;
TRUNCATE TABLE transactions RESTART IDENTITY;
TRUNCATE TABLE accounts RESTART IDENTITY;
TRUNCATE TABLE categories RESTART IDENTITY;

ALTER SEQUENCE categories RESTART WITH 1;
ALTER SEQUENCE transactions RESTART WITH 1;
ALTER SEQUENCE transfers RESTART WITH 1;
ALTER SEQUENCE users RESTART WITH 1;

DELETE FROM transfers;
DELETE FROM transfers WHERE id = 5;
DELETE FROM transactions WHERE id = 30;

--Be careful!!!
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;