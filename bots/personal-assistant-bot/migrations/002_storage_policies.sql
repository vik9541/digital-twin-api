-- ==========================================================
-- TASK-BOT-FIX-002: Настройка Storage Policies для bucket "project-files"
-- Дата: 14 декабря 2025
-- Выполнить в Supabase SQL Editor
-- ==========================================================

-- ==========================================
-- Storage Policies для bucket "project-files"
-- ==========================================

-- 1. Политика для ЗАГРУЗКИ файлов (INSERT)
-- Разрешаем всем загружать файлы (бот будет контролировать через API key)
CREATE POLICY "Allow uploads to project-files"
ON storage.objects
FOR INSERT
WITH CHECK (bucket_id = 'project-files');

-- 2. Политика для ОБНОВЛЕНИЯ файлов (UPDATE)
CREATE POLICY "Allow updates in project-files"
ON storage.objects
FOR UPDATE
USING (bucket_id = 'project-files');

-- 3. Политика для УДАЛЕНИЯ файлов (DELETE)
CREATE POLICY "Allow deletes in project-files"
ON storage.objects
FOR DELETE
USING (bucket_id = 'project-files');

-- 4. Политика для ЧТЕНИЯ файлов (SELECT) - публичный доступ
CREATE POLICY "Allow public read in project-files"
ON storage.objects
FOR SELECT
USING (bucket_id = 'project-files');

-- ==========================================
-- Дополнительный bucket для чеков (receipts)
-- ==========================================

-- Создаём bucket для чеков (если ещё не создан)
-- В Supabase Dashboard: Storage → New Bucket → "receipts" → Public

-- Политики для receipts bucket
CREATE POLICY "Allow uploads to receipts"
ON storage.objects
FOR INSERT
WITH CHECK (bucket_id = 'receipts');

CREATE POLICY "Allow updates in receipts"
ON storage.objects
FOR UPDATE
USING (bucket_id = 'receipts');

CREATE POLICY "Allow deletes in receipts"
ON storage.objects
FOR DELETE
USING (bucket_id = 'receipts');

CREATE POLICY "Allow public read in receipts"
ON storage.objects
FOR SELECT
USING (bucket_id = 'receipts');

-- ==========================================
-- ПРОВЕРКА: Показать все Storage политики
-- ==========================================
SELECT 
    policyname,
    tablename,
    cmd,
    qual
FROM pg_policies 
WHERE tablename = 'objects' 
AND schemaname = 'storage';

-- ==========================================
-- ГОТОВО! Storage настроен для бота.
-- ==========================================
