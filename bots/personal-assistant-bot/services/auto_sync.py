"""
Авто-синхронизация при старте и по расписанию
Запускается как фоновая задача
"""

import os
import asyncio
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from services.github_sync import get_github_sync, REPORTS_DIR

logger = logging.getLogger(__name__)

BOT_DIR = Path(__file__).parent.parent


class AutoSync:
    """Автоматическая синхронизация с GitHub"""
    
    def __init__(self):
        self.sync = get_github_sync()
        self.last_sync: Optional[datetime] = None
        self.sync_interval = timedelta(hours=1)  # Синхронизация каждый час
        self._task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Запуск фоновой синхронизации"""
        self._running = True
        
        # Первичная синхронизация
        await self.sync_all()
        
        # Запуск фоновой задачи
        self._task = asyncio.create_task(self._background_sync())
        logger.info("🔄 AutoSync запущен")
    
    async def stop(self):
        """Остановка"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🔄 AutoSync остановлен")
    
    async def _background_sync(self):
        """Фоновая синхронизация"""
        while self._running:
            await asyncio.sleep(self.sync_interval.total_seconds())
            
            if self._running:
                await self.sync_all()
    
    async def sync_all(self):
        """Полная синхронизация"""
        logger.info("🔄 Запуск синхронизации...")
        
        try:
            # 1. Загружаем ТЗ из GitHub
            await self.sync.sync_specs()
            
            # 2. Git pull (получаем последние изменения)
            self._git_pull()
            
            # 3. Загружаем отчёты в GitHub
            uploaded = await self.sync.sync_reports_to_github()
            if uploaded:
                logger.info(f"📤 Загружено отчётов: {uploaded}")
            
            # 4. Git push (если есть локальные изменения)
            self._git_push_if_needed()
            
            self.last_sync = datetime.now()
            logger.info(f"✅ Синхронизация завершена: {self.last_sync}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации: {e}")
    
    def _git_pull(self):
        """Git pull"""
        try:
            result = subprocess.run(
                ['git', 'pull', 'origin', 'main'],
                cwd=BOT_DIR,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                if 'Already up to date' not in result.stdout:
                    logger.info(f"📥 Git pull: {result.stdout.strip()}")
            else:
                logger.warning(f"Git pull warning: {result.stderr}")
        except Exception as e:
            logger.error(f"Git pull error: {e}")
    
    def _git_push_if_needed(self):
        """Git push если есть незакоммиченные изменения"""
        try:
            # Проверяем статус
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=BOT_DIR,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                # Есть изменения - коммитим и пушим
                subprocess.run(['git', 'add', '-A'], cwd=BOT_DIR)
                subprocess.run(
                    ['git', 'commit', '-m', f'auto: sync {datetime.now().strftime("%Y-%m-%d %H:%M")}'],
                    cwd=BOT_DIR,
                    capture_output=True
                )
                
                push_result = subprocess.run(
                    ['git', 'push', 'origin', 'main'],
                    cwd=BOT_DIR,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if push_result.returncode == 0:
                    logger.info("📤 Изменения отправлены в GitHub")
                else:
                    logger.warning(f"Git push warning: {push_result.stderr}")
        except Exception as e:
            logger.error(f"Git push error: {e}")
    
    def create_session_report(self, session_data: dict) -> Path:
        """Создать отчёт о сессии"""
        content = f"""# Отчёт о сессии

## Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Статистика:
- Сообщений обработано: {session_data.get('messages', 0)}
- Задач создано: {session_data.get('tasks_created', 0)}
- Контактов добавлено: {session_data.get('contacts_added', 0)}
- Рабочих записей: {session_data.get('work_logs', 0)}

## Ошибки:
{session_data.get('errors', 'Нет')}

## Примечания:
{session_data.get('notes', '')}
"""
        return self.sync.save_report('session', content, {
            'user_id': session_data.get('user_id', 'unknown')
        })


# Глобальный экземпляр
_auto_sync: Optional[AutoSync] = None


def get_auto_sync() -> AutoSync:
    """Получить экземпляр AutoSync"""
    global _auto_sync
    if _auto_sync is None:
        _auto_sync = AutoSync()
    return _auto_sync
