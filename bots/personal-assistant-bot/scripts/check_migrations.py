"""
Простой скрипт для проверки и показа непримененных миграций
Запуск: python scripts/check_migrations.py
"""

import os
import sys
from pathlib import Path

BOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BOT_DIR))

from dotenv import load_dotenv
load_dotenv(BOT_DIR / '.env')

from supabase import create_client

MIGRATIONS_DIR = BOT_DIR / 'migrations'
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')


def check_table_exists(client, table_name: str) -> bool:
    """Проверить существует ли таблица"""
    try:
        client.table(table_name).select('*').limit(1).execute()
        return True
    except Exception as e:
        if 'PGRST116' in str(e) or 'does not exist' in str(e).lower():
            return False
        # Таблица существует, но пустая или другая ошибка
        return True


def main():
    print("🔍 Проверка таблиц в Supabase...\n")
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Список всех таблиц которые должны быть
    required_tables = {
        '001': ['users', 'projects', 'health_entries', 'user_tasks', 'tasks', 'receipts', 'project_files', 'user_preferences'],
        '004': ['contacts'],
        '005': ['contact_interactions', 'work_logs', 'conversation_context'],
    }
    
    all_tables = []
    for tables in required_tables.values():
        all_tables.extend(tables)
    
    missing = []
    existing = []
    
    for table in all_tables:
        if check_table_exists(client, table):
            existing.append(table)
        else:
            missing.append(table)
    
    print(f"✅ Существующие таблицы ({len(existing)}):")
    for t in existing:
        print(f"   • {t}")
    
    if missing:
        print(f"\n❌ Отсутствующие таблицы ({len(missing)}):")
        for t in missing:
            print(f"   • {t}")
        
        print("\n📋 Нужно выполнить миграции:")
        
        # Определяем какие миграции нужны
        for migration_num, tables in required_tables.items():
            if any(t in missing for t in tables):
                migration_file = list(MIGRATIONS_DIR.glob(f'{migration_num}*.sql'))
                if migration_file:
                    print(f"   → {migration_file[0].name}")
        
        print(f"\n💡 Скопируй SQL из файлов миграций и выполни в:")
        print(f"   https://supabase.com/dashboard/project/lvixtpatqrtuwhygtpjx/sql/new")
    else:
        print("\n✨ Все таблицы созданы!")


if __name__ == '__main__':
    main()
