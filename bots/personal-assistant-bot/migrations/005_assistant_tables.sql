-- =============================================
-- Миграция 005: Таблицы для персонального ассистента
-- contact_interactions, work_logs, conversation_context
-- =============================================

-- История взаимодействий с контактами
CREATE TABLE IF NOT EXISTS contact_interactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    
    -- Тип взаимодействия
    interaction_type TEXT NOT NULL,  -- meeting, call, message, email, other
    
    -- Детали
    description TEXT,
    interaction_date TIMESTAMPTZ DEFAULT NOW(),
    
    -- Результат / договорённости
    outcome TEXT,
    follow_up_date DATE,
    follow_up_task TEXT,
    
    -- Метаданные
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для contact_interactions
CREATE INDEX IF NOT EXISTS idx_contact_interactions_user ON contact_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_contact_interactions_contact ON contact_interactions(contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_interactions_date ON contact_interactions(interaction_date DESC);

-- Учёт рабочего времени
CREATE TABLE IF NOT EXISTS work_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    
    -- Тип события
    log_type TEXT NOT NULL,  -- arrival, departure, break_start, break_end, overtime
    
    -- Время
    log_time TIME NOT NULL,
    log_date DATE DEFAULT CURRENT_DATE,
    
    -- Дополнительно
    notes TEXT,
    location TEXT,
    
    -- Метаданные
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индексы для work_logs
CREATE INDEX IF NOT EXISTS idx_work_logs_user ON work_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_work_logs_date ON work_logs(log_date DESC);
CREATE INDEX IF NOT EXISTS idx_work_logs_user_date ON work_logs(user_id, log_date);

-- Контекст разговора (для запоминания последнего упомянутого контакта и т.д.)
CREATE TABLE IF NOT EXISTS conversation_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL UNIQUE,
    
    -- Последний упомянутый контакт
    last_contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    last_contact_name TEXT,
    
    -- Последний интент
    last_intent TEXT,
    
    -- Контекст разговора (для многошаговых операций)
    context_data JSONB DEFAULT '{}',
    
    -- Время обновления
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Индекс для conversation_context
CREATE INDEX IF NOT EXISTS idx_conversation_context_user ON conversation_context(user_id);

-- RLS политики
ALTER TABLE contact_interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_context ENABLE ROW LEVEL SECURITY;

CREATE POLICY "allow_all_contact_interactions" ON contact_interactions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_work_logs" ON work_logs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_conversation_context" ON conversation_context FOR ALL USING (true) WITH CHECK (true);

-- =============================================
-- Готово! Выполни этот SQL в Supabase SQL Editor
-- =============================================
