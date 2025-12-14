"""
Базовые команды бота: /start, /help, /status
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update
from telegram.ext import ContextTypes

from services.supabase_service import SupabaseService


class CommandsHandler:
    """Обработчик базовых команд"""
    
    def __init__(self):
        self.db = SupabaseService()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start - короткое приветствие (Единое окно)"""
        user = update.effective_user
        user_id = str(user.id)
        first_name = user.first_name or "друг"
        
        # Создать/обновить пользователя в БД
        await self.db.ensure_user_exists(user_id)
        
        # Короткое приветствие без списка команд
        message = f"Привет, {first_name}! 👋\n\n"
        message += "Я твой личный ассистент.\n"
        message += "Просто напиши, что нужно:\n"
        message += "• \"запиши задачу: купить молоко\"\n"
        message += "• \"создай проект Ремонт\"\n"
        message += "• \"напомни через 30 мин позвонить\"\n"
        message += "• отправь фото чека\n"
        message += "• \"16:30 пошёл курить\"\n\n"
        message += "_/help — если нужна справка по командам_"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help - подробная справка"""
        message = "📖 **СПРАВКА ПО КОМАНДАМ**\n\n"
        
        message += "**🗂️ ПРОЕКТЫ**\n"
        message += "`/project list` - показать все проекты\n"
        message += "`/project add Название` - создать проект\n"
        message += "`/project info [ID]` - информация\n"
        message += "`/project done [ID]` - завершить\n\n"
        
        message += "**📋 ЗАДАЧИ**\n"
        message += "`/task list` - активные задачи\n"
        message += "`/task add Описание` - добавить\n"
        message += "`/task done [#]` - выполнить\n"
        message += "`/task priority [#] high` - приоритет\n\n"
        
        message += "**🧾 ЧЕКИ**\n"
        message += "📸 Отправь фото чека\n"
        message += "`/receipt history` - история\n"
        message += "`/receipt stats` - статистика\n\n"
        
        message += "**💪 ЗДОРОВЬЕ**\n"
        message += "_Съел яблоко_, _Пробежал 5 км_\n"
        message += "`/health report` - за день\n"
        message += "`/health week` - за неделю\n\n"
        
        message += "**⏰ НАПОМИНАНИЯ**\n"
        message += "`/remind через 30 мин Текст`\n"
        message += "`/remind в 15:00 Созвон`\n"
        message += "`/remind list` - список\n\n"
        
        message += "**📤 ЭКСПОРТ**\n"
        message += "`/export tasks` - задачи CSV\n"
        message += "`/export all` - полный бэкап\n"
        message += "`/report month` - отчет за месяц\n"
        message += "`/report tips` - советы\n\n"
        
        message += "**🔷 MICROSOFT**\n"
        message += "`/ms auth TOKEN` - авторизация\n"
        message += "`/ms contacts` - контакты\n"
        message += "`/ms calendar` - календарь\n\n"
        
        message += "**⚙️ РЕЖИМЫ**\n"
        message += "`/mode executor` - без советов\n"
        message += "`/mode advisor` - с советами\n"
        message += "`/settings` - настройки\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /status - статус пользователя"""
        user_id = str(update.effective_user.id)
        
        # Получить статистику
        stats = await self.db.get_user_stats(user_id)
        prefs = await self.db.get_user_preferences(user_id)
        
        message = "📊 **ТВОЙ СТАТУС**\n\n"
        message += f"📂 Проектов: {stats.get('projects_count', 0)}\n"
        message += f"   └ Активных: {stats.get('active_projects', 0)}\n"
        message += f"📋 Задач: {stats.get('tasks_count', 0)}\n"
        message += f"   └ В работе: {stats.get('pending_tasks', 0)}\n"
        message += f"🧾 Чеков: {stats.get('receipts_count', 0)}\n"
        message += f"💪 Записей в дневнике: {stats.get('health_entries', 0)}\n\n"
        message += f"⚙️ Режим: `{prefs.get('mode', 'executor')}`\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
