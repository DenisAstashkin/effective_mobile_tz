TRUNCATE TABLE access_rules RESTART IDENTITY CASCADE;
TRUNCATE TABLE resources RESTART IDENTITY CASCADE;
TRUNCATE TABLE users RESTART IDENTITY CASCADE;

INSERT INTO resources (name) VALUES 
('document'),
('access_rules');

INSERT INTO users (full_name, email, password_hash, is_active, created_at) VALUES 
(
    'Главный Администратор', 
    'admin@test.com', 
    'pbkdf2_sha256$1200000$YH1lg8R4SiZGcyB9y1KsSz$8B9X+TUGS8xn2Q2a/aVonF5MCGfEP9Y4N93bQhT9zGg=', -- admin123
    true, 
    CURRENT_TIMESTAMP
),
(
    'Менеджер Петр', 
    'manager@test.com', 
    'pbkdf2_sha256$1200000$3ES87VtFSqwJLAmWLVlrC8$ynp53XVZ/chzOW1k7V+ECZo2bjTvCIGnx1xTzWmIbdU=', -- manager123
    true, 
    CURRENT_TIMESTAMP
);

INSERT INTO access_rules (
    user_id, resource_id, 
    read_all_permission, read_own_permission, create_permission, 
    update_all_permission, update_own_permission, 
    delete_all_permission, delete_own_permission, 
    is_admin_permission
) VALUES 
(1, 1, false, false, false, false, false, false, false, true),
(1, 2, false, false, false, false, false, false, false, true);

INSERT INTO access_rules (
    user_id, resource_id, 
    read_all_permission, read_own_permission, create_permission, 
    update_all_permission, update_own_permission, 
    delete_all_permission, delete_own_permission, 
    is_admin_permission
) VALUES 
(2, 1, false, true, true, false, true, false, true, false);

