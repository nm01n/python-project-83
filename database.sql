DROP TABLE IF EXISTS urls;

-- Создаем таблицу urls
CREATE TABLE urls (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL
);
