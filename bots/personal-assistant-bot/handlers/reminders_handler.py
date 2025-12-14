"""
Обработчик напоминаний
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from services.notifications import NotificationService

logger = logging.getLogger(__name__)


class RemindersHandler:
    """Обработчик команд напоминаний"""
    
    def __init__(self, notification_service: NotificationService = None):
        self.notifications = notification_service
    
    def set_notification_service(self, service: NotificationService):
        """Установить сервис уведомлений"""
        self.notifications = service
    
    async def remind_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Добавить напоминание
        /remind через 30 минут Позвонить маме
        /remind в 15:00 Созвон с командой
        /remind завтра в 10:00 Сдать отчет
        """
        if not context.args:
            await update.message.reply_text(
                "⏰ **НАПОМИНАНИЯ**\n\n"
                "Примеры:\n"
                "• `/remind через 30 минут Позвонить`\n"
                "• `/remind в 15:00 Созвон`\n"
                "• `/remind завтра в 10:00 Отчет`\n\n"
                "Команды:\n"
                "• `/remind list` - список напоминаний\n"
                "• `/remind delete ID` - удалить",
                parse_mode='Markdown'
            )
            return
        
        user_id = str(update.effective_user.id)
        text = ' '.join(context.args)
        
        # Проверка подкоманд
        if text.lower().startswith('list'):
            await self.remind_list(update, context)
            return
        elif text.lower().startswith('delete'):
            await self.remind_delete(update, context)
            return
        
        if not self.notifications:
            await update.message.reply_text("❌ Сервис напоминаний не настроен")
            return
        
        # Парсинг времени
        remind_time = self.notifications.parse_reminder_time(text)
        
        if not remind_time:
            await update.message.reply_text(
                "❌ Не удалось распознать время.\n\n"
                "Используйте форматы:\n"
                "• `через 30 минут`\n"
                "• `через 2 часа`\n"
                "• `в 15:00`\n"
                "• `завтра в 10:00`",
                parse_mode='Markdown'
            )
            return
        
        # Извлечение текста напоминания (убираем время)
        import re
        reminder_text = re.sub(
            r'(через\s+\d+\s*(минут|мин|час|часов|часа)|завтра\s+в?\s*\d{1,2}:\d{2}|в\s*\d{1,2}:\d{2}|\d{1,2}:\d{2})',
            '',
            text,
            flags=re.IGNORECASE
        ).strip()
        
        if not reminder_text:
            reminder_text = "Напоминание"
        
        # Создание напоминания
        reminder = self.notifications.add_reminder(
            user_id=user_id,
            text=reminder_text,
            remind_at=remind_time
        )
        
        await update.message.reply_text(
            f"✅ **Напоминание создано!**\n\n"
            f"📝 {reminder_text}\n"
            f"⏰ {remind_time.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"ID: `{reminder.id[:8]}`",
            parse_mode='Markdown'
        )
    
    async def remind_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Список напоминаний"""
        user_id = str(update.effective_user.id)
        
        if not self.notifications:
            await update.message.reply_text("❌ Сервис напоминаний не настроен")
            return
        
        reminders = self.notifications.get_user_reminders(user_id)
        
        if not reminders:
            await update.message.reply_text("📭 У тебя нет активных напоминаний")
            return
        
        lines = ["⏰ **ТВОИ НАПОМИНАНИЯ:**\n"]
        
        for r in sorted(reminders, key=lambda x: x.remind_at):
            lines.append(
                f"• {r.text}\n"
                f"  📅 {r.remind_at.strftime('%d.%m %H:%M')} | ID: `{r.id[:8]}`"
            )
        
        await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
    
    async def remind_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить напоминание"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Укажи ID напоминания\n"
                "Пример: `/remind delete abc12345`",
                parse_mode='Markdown'
            )
            return
        
        reminder_id_prefix = context.args[1]
        user_id = str(update.effective_user.id)
        
        if not self.notifications:
            await update.message.reply_text("❌ Сервис напоминаний не настроен")
            return
        
        # Поиск по префиксу ID
        reminders = self.notifications.get_user_reminders(user_id)
        target = None
        
        for r in reminders:
            if r.id.startswith(reminder_id_prefix):
                target = r
                break
        
        if not target:
            await update.message.reply_text("❌ Напоминание не найдено")
            return
        
        self.notifications.remove_reminder(target.id)
        
        await update.message.reply_text(
            f"✅ Напоминание удалено:\n_{target.text}_",
            parse_mode='Markdown'
        )
