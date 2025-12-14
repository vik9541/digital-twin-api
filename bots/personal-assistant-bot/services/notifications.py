"""
Сервис напоминаний и уведомлений
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Reminder:
    """Структура напоминания"""
    id: str
    user_id: str
    text: str
    remind_at: datetime
    repeat: Optional[str] = None  # daily, weekly, monthly, None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    REPEAT_OPTIONS = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30)
    }


class NotificationService:
    """Сервис уведомлений и напоминаний"""
    
    def __init__(self, send_callback: Callable):
        """
        Args:
            send_callback: Асинхронная функция для отправки сообщений
                          send_callback(user_id, text)
        """
        self.send_callback = send_callback
        self.reminders: Dict[str, Reminder] = {}
        self._running = False
        self._task = None
    
    async def start(self):
        """Запуск сервиса уведомлений"""
        self._running = True
        self._task = asyncio.create_task(self._check_loop())
        logger.info("🔔 Notification service started")
    
    async def stop(self):
        """Остановка сервиса"""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("🔔 Notification service stopped")
    
    async def _check_loop(self):
        """Цикл проверки напоминаний"""
        while self._running:
            try:
                await self._check_reminders()
                await asyncio.sleep(60)  # Проверка каждую минуту
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Reminder check error: {e}")
                await asyncio.sleep(60)
    
    async def _check_reminders(self):
        """Проверка и отправка напоминаний"""
        now = datetime.now()
        
        for reminder_id, reminder in list(self.reminders.items()):
            if not reminder.is_active:
                continue
            
            if reminder.remind_at <= now:
                # Отправить напоминание
                await self._send_reminder(reminder)
                
                # Обработка повторения
                if reminder.repeat and reminder.repeat in Reminder.REPEAT_OPTIONS:
                    delta = Reminder.REPEAT_OPTIONS[reminder.repeat]
                    reminder.remind_at = now + delta
                else:
                    reminder.is_active = False
    
    async def _send_reminder(self, reminder: Reminder):
        """Отправка напоминания пользователю"""
        try:
            message = f"⏰ **НАПОМИНАНИЕ**\n\n{reminder.text}"
            await self.send_callback(reminder.user_id, message)
            logger.info(f"Reminder sent to {reminder.user_id}: {reminder.text[:50]}")
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")
    
    def add_reminder(
        self,
        user_id: str,
        text: str,
        remind_at: datetime,
        repeat: str = None
    ) -> Reminder:
        """Добавить напоминание"""
        import uuid
        
        reminder = Reminder(
            id=str(uuid.uuid4()),
            user_id=user_id,
            text=text,
            remind_at=remind_at,
            repeat=repeat
        )
        
        self.reminders[reminder.id] = reminder
        logger.info(f"Reminder added: {reminder.id} for {user_id}")
        
        return reminder
    
    def remove_reminder(self, reminder_id: str) -> bool:
        """Удалить напоминание"""
        if reminder_id in self.reminders:
            del self.reminders[reminder_id]
            return True
        return False
    
    def get_user_reminders(self, user_id: str) -> List[Reminder]:
        """Получить напоминания пользователя"""
        return [
            r for r in self.reminders.values()
            if r.user_id == user_id and r.is_active
        ]
    
    def parse_reminder_time(self, text: str) -> Optional[datetime]:
        """
        Парсинг времени из текста
        
        Поддерживает:
        - "через 5 минут"
        - "через 2 часа"
        - "завтра в 10:00"
        - "15:30"
        """
        import re
        
        now = datetime.now()
        
        # "через N минут/часов"
        match = re.search(r'через\s+(\d+)\s*(минут|мин|час|часов|часа)', text.lower())
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            
            if 'мин' in unit:
                return now + timedelta(minutes=amount)
            elif 'час' in unit:
                return now + timedelta(hours=amount)
        
        # "завтра в HH:MM"
        match = re.search(r'завтра\s+в?\s*(\d{1,2}):(\d{2})', text.lower())
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            tomorrow = now + timedelta(days=1)
            return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # "в HH:MM" (сегодня)
        match = re.search(r'в\s*(\d{1,2}):(\d{2})', text.lower())
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Если время уже прошло - на завтра
            if target <= now:
                target += timedelta(days=1)
            
            return target
        
        # Просто HH:MM
        match = re.search(r'^(\d{1,2}):(\d{2})$', text.strip())
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if target <= now:
                target += timedelta(days=1)
            
            return target
        
        return None


class DailyDigest:
    """Ежедневный дайджест для пользователя"""
    
    def __init__(self, supabase_service, send_callback: Callable):
        self.db = supabase_service
        self.send_callback = send_callback
    
    async def generate_digest(self, user_id: str) -> str:
        """Генерация ежедневного дайджеста"""
        
        lines = ["🌅 **ДОБРОЕ УТРО!**\n"]
        
        # Задачи на сегодня
        tasks = await self.db.get_user_tasks(user_id, status='pending')
        if tasks:
            lines.append(f"📋 **Задач на сегодня:** {len(tasks)}")
            
            # Показать важные
            high_priority = [t for t in tasks if t.get('priority') == 'high']
            if high_priority:
                lines.append(f"  🔴 Важных: {len(high_priority)}")
        else:
            lines.append("✅ Нет активных задач!")
        
        # Активные проекты
        projects = await self.db.get_user_projects(user_id, status='active')
        if projects:
            lines.append(f"\n📂 **Активных проектов:** {len(projects)}")
        
        # Траты за вчера
        from datetime import date
        yesterday = date.today() - timedelta(days=1)
        receipts = await self.db.get_user_receipts(user_id, limit=100)
        
        yesterday_receipts = [
            r for r in receipts
            if r.get('created_at', '').startswith(str(yesterday))
        ]
        
        if yesterday_receipts:
            total = sum(r.get('total_sum', 0) for r in yesterday_receipts)
            lines.append(f"\n💰 **Вчера потрачено:** {total:.0f}₽")
        
        lines.append("\n🚀 Хорошего дня!")
        
        return "\n".join(lines)
    
    async def send_digest(self, user_id: str):
        """Отправить дайджест пользователю"""
        digest = await self.generate_digest(user_id)
        await self.send_callback(user_id, digest)
