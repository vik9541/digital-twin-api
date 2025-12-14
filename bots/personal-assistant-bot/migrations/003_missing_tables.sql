-- ==========================================================
-- Создание недостающих таблиц для Personal Assistant Bot
-- Дата: 14 декабря 2025
-- Выполнить в Supabase SQL Editor
-- ==========================================================

-- ==========================================
-- 1. Таблица пользователей (users)
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id VARCHAR UNIQUE NOT NULL,
    first_name VARCHAR,
    last_name VARCHAR,
    username VARCHAR,
    language_code VARCHAR DEFAULT 'ru',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- ==========================================
-- 2. Таблица проектов (projects) 
-- Если уже есть user_projects - создаём VIEW
-- ==========================================
-- Вариант A: Создать новую таблицу
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    project_name VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR DEFAULT 'active', -- active, done, archived
    created_at TIMESTAMP DEFAULT NOW(),
    deadline TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- ==========================================
-- 3. Дневник здоровья (health_entries)
-- ==========================================
CREATE TABLE IF NOT EXISTS health_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    entry_date DATE DEFAULT CURRENT_DATE,
    entry_time TIME DEFAULT CURRENT_TIME,
    entry_type VARCHAR, -- food, activity, habit, mood, sleep, measurement
    description TEXT,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_health_entries_user_id ON health_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_health_entries_entry_date ON health_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_health_entries_entry_type ON health_entries(entry_type);

-- ==========================================
-- 4. RLS (Row Level Security) 
-- ==========================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_entries ENABLE ROW LEVEL SECURITY;

-- Политики для service_role (полный доступ)
-- Service role обходит RLS автоматически

-- ==========================================
-- 5. Политики для анонимных пользователей (опционально)
-- ==========================================
-- Если нужен доступ через anon key:
/*
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (true);

CREATE POLICY "Users can insert own data" ON users
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (true);

CREATE POLICY "Projects owner access" ON projects
    FOR ALL USING (true);

CREATE POLICY "Health entries owner access" ON health_entries
    FOR ALL USING (true);
*/

-- ==========================================
-- Готово! Проверка:
-- ==========================================
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
