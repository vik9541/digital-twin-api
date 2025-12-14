"""
Скрипт для автоматического применения SQL миграций к Supabase
Запуск: python scripts/run_migrations.py
"""

import os
import sys
from pathlib import Path

# Добавляем путь для импортов
BOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BOT_DIR))

from dotenv import load_dotenv
load_dotenv(BOT_DIR / '.env')

from supabase import create_client

# Конфигурация
MIGRATIONS_DIR = BOT_DIR / 'migrations'
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


def get_applied_migrations(client) -> set:
    """Получить список уже применённых миграций"""
    try:
        # Создаём таблицу для отслеживания миграций если её нет
        client.postgrest.rpc('exec_sql', {
            'sql': '''
                CREATE TABLE IF NOT EXISTS _migrations (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    applied_at TIMESTAMPTZ DEFAULT NOW()
                );
            '''
        }).execute()
    except Exception:
        pass  # Таблица может уже существовать
    
    try:
        result = client.table('_migrations').select('name').execute()
        return {row['name'] for row in result.data}
    except Exception:
        return set()


def apply_migration(client, migration_file: Path) -> bool:
    """Применить миграцию"""
    migration_name = migration_file.name
    
    print(f"📄 Применяю миграцию: {migration_name}")
    
    try:
        sql_content = migration_file.read_text(encoding='utf-8')
        
        # Выполняем SQL через REST API
        # Supabase не позволяет выполнять произвольный SQL через клиент
        # Поэтому используем psycopg2 напрямую
        
        import psycopg2
        
        # Парсим DATABASE_URL из SUPABASE_URL
        # Формат: https://xxx.supabase.co -> postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres
        project_ref = SUPABASE_URL.replace('https://', '').replace('.supabase.co', '')
        
        # Нужен DATABASE_URL или пароль от БД
        db_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        if not db_password:
            print(f"⚠️  Для автоматических миграций нужен SUPABASE_DB_PASSWORD в .env")
            print(f"   Выполни SQL вручную в Supabase SQL Editor:")
            print(f"   {migration_file}")
            return False
        
        conn_string = f"postgresql://postgres.{project_ref}:{db_password}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres"
        
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        
        with conn.cursor() as cur:
            cur.execute(sql_content)
        
        conn.close()
        
        # Записываем в таблицу миграций
        client.table('_migrations').insert({'name': migration_name}).execute()
        
        print(f"✅ Миграция {migration_name} применена успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при применении {migration_name}: {e}")
        return False


def run_migrations():
    """Запустить все непримененные миграции"""
    print("🚀 Запуск миграций Supabase...")
    print(f"📁 Директория миграций: {MIGRATIONS_DIR}")
    print()
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Не заданы SUPABASE_URL и SUPABASE_KEY в .env")
        return
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Получаем список файлов миграций
    migration_files = sorted(MIGRATIONS_DIR.glob('*.sql'))
    
    if not migration_files:
        print("📭 Нет файлов миграций")
        return
    
    print(f"📋 Найдено миграций: {len(migration_files)}")
    
    # Получаем уже применённые
    applied = get_applied_migrations(client)
    print(f"✅ Уже применено: {len(applied)}")
    print()
    
    # Применяем новые
    new_count = 0
    for migration_file in migration_files:
        if migration_file.name not in applied:
            if apply_migration(client, migration_file):
                new_count += 1
            print()
    
    if new_count == 0:
        print("✨ Все миграции уже применены!")
    else:
        print(f"🎉 Применено новых миграций: {new_count}")


def show_pending():
    """Показать непримененные миграции"""
    print("📋 Проверка миграций...")
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    applied = get_applied_migrations(client)
    
    migration_files = sorted(MIGRATIONS_DIR.glob('*.sql'))
    
    pending = [f for f in migration_files if f.name not in applied]
    
    if pending:
        print(f"\n⏳ Непримененные миграции ({len(pending)}):")
        for f in pending:
            print(f"   - {f.name}")
        print(f"\nВыполни их в Supabase SQL Editor или добавь SUPABASE_DB_PASSWORD в .env")
    else:
        print("✨ Все миграции применены!")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--check':
        show_pending()
    else:
        run_migrations()
