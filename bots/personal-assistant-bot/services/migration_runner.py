"""
Автоматические миграции при старте бота
Использует Supabase Management API для выполнения SQL
"""

import os
import sys
import logging
import httpx
from pathlib import Path
from typing import Set, List

logger = logging.getLogger(__name__)


class MigrationRunner:
    """Автоматический запуск миграций"""
    
    def __init__(self, migrations_dir: Path):
        self.migrations_dir = migrations_dir
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.db_password = os.getenv('SUPABASE_DB_PASSWORD')
        
        # Извлекаем project_ref из URL
        # https://lvixtpatqrtuwhygtpjx.supabase.co -> lvixtpatqrtuwhygtpjx
        if self.supabase_url:
            self.project_ref = self.supabase_url.replace('https://', '').split('.')[0]
        else:
            self.project_ref = None
    
    def _get_supabase_client(self):
        """Создать клиент Supabase"""
        from supabase import create_client
        return create_client(self.supabase_url, self.supabase_key)
    
    def _ensure_migrations_table(self, client) -> bool:
        """Создать таблицу отслеживания миграций"""
        try:
            # Пробуем прочитать - если ошибка, таблицы нет
            client.table('_migrations').select('name').limit(1).execute()
            return True
        except Exception as e:
            if 'does not exist' in str(e).lower() or 'PGRST116' in str(e):
                # Таблицы нет - нужно создать через SQL
                logger.warning("Таблица _migrations не существует. Создай её вручную или через SQL Editor.")
                return False
            return True
    
    def _get_applied_migrations(self, client) -> Set[str]:
        """Получить список применённых миграций"""
        try:
            result = client.table('_migrations').select('name').execute()
            return {row['name'] for row in result.data}
        except Exception:
            return set()
    
    def _mark_migration_applied(self, client, name: str):
        """Отметить миграцию как применённую"""
        try:
            client.table('_migrations').insert({'name': name}).execute()
        except Exception as e:
            logger.error(f"Не удалось записать миграцию {name}: {e}")
    
    def _check_tables_exist(self, client, tables: List[str]) -> List[str]:
        """Проверить какие таблицы существуют"""
        existing = []
        for table in tables:
            try:
                client.table(table).select('*').limit(1).execute()
                existing.append(table)
            except Exception:
                pass
        return existing
    
    def _get_migration_tables(self, migration_name: str) -> List[str]:
        """Получить список таблиц из миграции"""
        tables_map = {
            '001': ['users', 'projects', 'health_entries', 'user_tasks', 'tasks', 'receipts', 'project_files', 'user_preferences'],
            '002': [],  # Storage policies
            '003': [],  # Other
            '004': ['contacts'],
            '005': ['contact_interactions', 'work_logs', 'conversation_context'],
        }
        
        prefix = migration_name.split('_')[0]
        return tables_map.get(prefix, [])
    
    def check_and_report(self) -> dict:
        """Проверить статус миграций и вернуть отчёт"""
        client = self._get_supabase_client()
        
        migration_files = sorted(self.migrations_dir.glob('*.sql'))
        applied = self._get_applied_migrations(client)
        
        result = {
            'total': len(migration_files),
            'applied': [],
            'pending': [],
            'missing_tables': []
        }
        
        all_required_tables = []
        
        for mf in migration_files:
            tables = self._get_migration_tables(mf.name)
            all_required_tables.extend(tables)
            
            if mf.name in applied:
                result['applied'].append(mf.name)
            else:
                # Проверяем существуют ли таблицы
                existing = self._check_tables_exist(client, tables)
                if set(existing) == set(tables) and tables:
                    # Все таблицы есть - миграция фактически применена
                    result['applied'].append(mf.name)
                    self._mark_migration_applied(client, mf.name)
                else:
                    result['pending'].append(mf.name)
                    result['missing_tables'].extend([t for t in tables if t not in existing])
        
        return result
    
    def run_on_startup(self) -> bool:
        """Запустить проверку при старте бота"""
        logger.info("🔍 Проверка миграций базы данных...")
        
        try:
            status = self.check_and_report()
            
            if status['pending']:
                logger.warning(f"⚠️  Есть непримененные миграции: {status['pending']}")
                if status['missing_tables']:
                    logger.warning(f"❌ Отсутствующие таблицы: {status['missing_tables']}")
                    logger.warning("   Выполни SQL миграции в Supabase SQL Editor!")
                    return False
            else:
                logger.info(f"✅ Все миграции применены ({status['total']} шт.)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки миграций: {e}")
            return False


def run_migrations_check():
    """Функция для вызова из main.py"""
    from pathlib import Path
    
    bot_dir = Path(__file__).parent.parent
    migrations_dir = bot_dir / 'migrations'
    
    runner = MigrationRunner(migrations_dir)
    return runner.run_on_startup()
