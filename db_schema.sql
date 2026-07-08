-- Создание БД
CREATE DATABASE effective_db
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Russian_Russia.1251'
    LC_CTYPE = 'Russian_Russia.1251'
    LOCALE_PROVIDER = 'libc'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

-- Таблица пользователей
CREATE TABLE Users(
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица токенов
CREATE TABLE User_sessions(
    token VARCHAR(64) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL
);

-- Таблица ресурсов
CREATE TABLE Resources(
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Таблица матрицы прав доступа (RBAC/ABAC)
CREATE TABLE Access_rules(
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES Users(id) ON DELETE CASCADE,
    resource_id INT NOT NULL REFERENCES Resources(id) ON DELETE CASCADE,
    read_all_permission BOOLEAN DEFAULT FALSE NOT NULL,
    read_own_permission BOOLEAN DEFAULT FALSE NOT NULL,
    create_permission BOOLEAN DEFAULT FALSE NOT NULL,
    update_all_permission BOOLEAN DEFAULT FALSE NOT NULL,
    update_own_permission BOOLEAN DEFAULT FALSE NOT NULL,
    delete_all_permission BOOLEAN DEFAULT FALSE NOT NULL,
    delete_own_permission BOOLEAN DEFAULT FALSE NOT NULL,
    is_admin_permission BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT unique_user_resource UNIQUE (user_id, resource_id)
);