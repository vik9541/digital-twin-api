-- =============================================
-- Миграция 004: Таблица контактов
-- =============================================

-- Таблица контактов
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    
    -- Основная информация
    display_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    nickname TEXT,
    
    -- Контактные данные
    phone TEXT,
    phone_work TEXT,
    email TEXT,
    email_work TEXT,
    
    -- Дополнительно
    company TEXT,
    job_title TEXT,
    birthday DATE,
    notes TEXT,
    
    -- Категоризация
    category TEXT DEFAULT 'personal',  -- personal, work, family, friend, other
    is_favorite BOOLEAN DEFAULT FALSE,
    
    -- Метаданные
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_contacts_user_id ON contacts(user_id);
CREATE INDEX IF NOT EXISTS idx_contacts_display_name ON contacts(display_name);
CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone);
CREATE INDEX IF NOT EXISTS idx_contacts_category ON contacts(category);
CREATE INDEX IF NOT EXISTS idx_contacts_is_favorite ON contacts(is_favorite);

-- Полнотекстовый поиск
CREATE INDEX IF NOT EXISTS idx_contacts_search ON contacts 
USING GIN (to_tsvector('russian', coalesce(display_name, '') || ' ' || coalesce(phone, '') || ' ' || coalesce(notes, '')));

-- RLS политики
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;

-- Политика: пользователи видят только свои контакты
CREATE POLICY "Users can view own contacts" ON contacts
    FOR SELECT USING (true);

CREATE POLICY "Users can insert own contacts" ON contacts
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update own contacts" ON contacts
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete own contacts" ON contacts
    FOR DELETE USING (true);

-- Триггер для обновления updated_at
CREATE OR REPLACE FUNCTION update_contacts_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW
    EXECUTE FUNCTION update_contacts_updated_at();

-- =============================================
-- Готово! Выполни этот SQL в Supabase SQL Editor
-- =============================================
