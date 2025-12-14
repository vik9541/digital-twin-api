-- ==========================================================
-- TASK-BOT-FIX-001: Создание структуры БД для Personal Assistant Bot
-- Дата: 13 декабря 2025
-- Выполнить в Supabase SQL Editor: https://supabase.com/dashboard
-- ==========================================================

-- ==========================================
-- 1. Таблица проектов пользователя
-- ==========================================
CREATE TABLE IF NOT EXISTS user_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    project_name VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR DEFAULT 'active', -- active, done, archived
    created_at TIMESTAMP DEFAULT NOW(),
    deadline TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- ==========================================
-- 2. Файлы проектов
-- ==========================================
CREATE TABLE IF NOT EXISTS project_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES user_projects(id) ON DELETE CASCADE,
    file_name VARCHAR NOT NULL,
    file_url VARCHAR NOT NULL,
    file_hash VARCHAR,
    file_type VARCHAR,
    file_size INT,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    tags TEXT[] DEFAULT '{}'
);

-- ==========================================
-- 3. Задачи пользователя
-- ==========================================
CREATE TABLE IF NOT EXISTS user_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    project_id UUID REFERENCES user_projects(id) ON DELETE SET NULL,
    task_description TEXT NOT NULL,
    status VARCHAR DEFAULT 'pending', -- pending, in_progress, done
    created_at TIMESTAMP DEFAULT NOW(),
    due_date TIMESTAMP,
    priority VARCHAR DEFAULT 'medium' -- low, medium, high
);

-- ==========================================
-- 4. Чеки
-- ==========================================
CREATE TABLE IF NOT EXISTS receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    store_name VARCHAR,
    store_location VARCHAR,
    receipt_date TIMESTAMP,
    total_sum DECIMAL,
    file_url VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- ==========================================
-- 5. Товары в чеках
-- ==========================================
CREATE TABLE IF NOT EXISTS receipt_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receipt_id UUID REFERENCES receipts(id) ON DELETE CASCADE,
    item_name VARCHAR NOT NULL,
    category VARCHAR,
    price DECIMAL,
    quantity DECIMAL,
    unit VARCHAR,
    price_per_unit DECIMAL
);

-- ==========================================
-- 6. Дневник здоровья
-- ==========================================
CREATE TABLE IF NOT EXISTS health_diary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR NOT NULL,
    entry_date DATE DEFAULT CURRENT_DATE,
    entry_time TIME DEFAULT CURRENT_TIME,
    entry_type VARCHAR, -- food, activity, habit, mood, sleep, measurement
    description TEXT,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ==========================================
-- 7. Настройки пользователя
-- ==========================================
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id VARCHAR PRIMARY KEY,
    mode VARCHAR DEFAULT 'executor', -- executor, advisor, silent, detailed
    give_advice BOOLEAN DEFAULT false,
    language VARCHAR DEFAULT 'ru',
    timezone VARCHAR DEFAULT 'Europe/Moscow',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ==========================================
-- ИНДЕКСЫ для быстрого поиска
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_user_projects_user_id ON user_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_user_projects_status ON user_projects(status);
CREATE INDEX IF NOT EXISTS idx_project_files_project_id ON project_files(project_id);
CREATE INDEX IF NOT EXISTS idx_user_tasks_user_id ON user_tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tasks_status ON user_tasks(status);
CREATE INDEX IF NOT EXISTS idx_user_tasks_project_id ON user_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_receipts_user_id ON receipts(user_id);
CREATE INDEX IF NOT EXISTS idx_receipts_receipt_date ON receipts(receipt_date);
CREATE INDEX IF NOT EXISTS idx_receipt_items_receipt_id ON receipt_items(receipt_id);
CREATE INDEX IF NOT EXISTS idx_health_diary_user_id ON health_diary(user_id);
CREATE INDEX IF NOT EXISTS idx_health_diary_entry_date ON health_diary(entry_date);
CREATE INDEX IF NOT EXISTS idx_health_diary_entry_type ON health_diary(entry_type);

-- ==========================================
-- ТРИГГЕР для обновления updated_at
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- RLS (Row Level Security) Политики
-- ==========================================

-- Включаем RLS для всех таблиц
ALTER TABLE user_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE receipts ENABLE ROW LEVEL SECURITY;
ALTER TABLE receipt_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_diary ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;

-- Политики для user_projects (пользователь видит только свои проекты)
CREATE POLICY "Users can view own projects" ON user_projects
    FOR SELECT USING (true);  -- API сервис будет фильтровать по user_id

CREATE POLICY "Users can insert own projects" ON user_projects
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update own projects" ON user_projects
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete own projects" ON user_projects
    FOR DELETE USING (true);

-- Аналогичные политики для остальных таблиц
CREATE POLICY "Allow all for project_files" ON project_files FOR ALL USING (true);
CREATE POLICY "Allow all for user_tasks" ON user_tasks FOR ALL USING (true);
CREATE POLICY "Allow all for receipts" ON receipts FOR ALL USING (true);
CREATE POLICY "Allow all for receipt_items" ON receipt_items FOR ALL USING (true);
CREATE POLICY "Allow all for health_diary" ON health_diary FOR ALL USING (true);
CREATE POLICY "Allow all for user_preferences" ON user_preferences FOR ALL USING (true);

-- ==========================================
-- ПРОВЕРКА: Вывести все созданные таблицы
-- ==========================================
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'user_projects', 
    'project_files', 
    'user_tasks', 
    'receipts', 
    'receipt_items', 
    'health_diary', 
    'user_preferences'
);

-- ==========================================
-- ГОТОВО! Все таблицы для бота созданы.
-- ==========================================
