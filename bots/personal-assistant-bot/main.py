"""
Personal Assistant Bot - Главная точка входа
"""

import os
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from .config import config
from .handlers import (
    CommandsHandler,
    ProjectsHandler,
    TasksHandler,
    ReceiptsHandler,
    HealthHandler,
    SettingsHandler,
    RemindersHandler,
    ExportHandler,
    MicrosoftHandler
)
from .services.notifications import NotificationService

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class PersonalAssistantBot:
    """Главный класс бота"""
    
    def __init__(self, application: Application = None):
        self.application = application
        self.commands = CommandsHandler()
        self.projects = ProjectsHandler()
        self.tasks = TasksHandler()
        self.receipts = ReceiptsHandler()
        self.health = HealthHandler()
        self.settings = SettingsHandler()
        self.reminders = RemindersHandler()
        self.export = ExportHandler()
        self.microsoft = MicrosoftHandler()
        
        # Сервис уведомлений
        self.notification_service = None
    
    async def _send_notification(self, user_id: str, text: str):
        """Отправка уведомления пользователю"""
        if self.application:
            try:
                await self.application.bot.send_message(
                    chat_id=int(user_id),
                    text=text,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
    
    async def start_notification_service(self):
        """Запуск сервиса уведомлений"""
        self.notification_service = NotificationService(self._send_notification)
        self.reminders.set_notification_service(self.notification_service)
        await self.notification_service.start()
    
    async def stop_notification_service(self):
        """Остановка сервиса уведомлений"""
        if self.notification_service:
            await self.notification_service.stop()
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений (дневник здоровья)"""
        # Попробовать обработать как запись о здоровье
        handled = await self.health.handle_health_message(update, context)
        
        if not handled:
            # Если не распознано - вывести подсказку
            await update.message.reply_text(
                "🤔 Не понял команду.\n\n"
                "Попробуй:\n"
                "• `/help` - список команд\n"
                "• Напиши что съел/сделал для дневника здоровья",
                parse_mode='Markdown'
            )
    
    def setup_handlers(self, app: Application):
        """Настройка обработчиков команд"""
        
        # Базовые команды
        app.add_handler(CommandHandler("start", self.commands.start))
        app.add_handler(CommandHandler("help", self.commands.help))
        app.add_handler(CommandHandler("status", self.commands.status))
        
        # Проекты
        app.add_handler(CommandHandler("project", self._route_project_command))
        
        # Задачи
        app.add_handler(CommandHandler("task", self._route_task_command))
        
        # Чеки
        app.add_handler(CommandHandler("receipt", self._route_receipt_command))
        app.add_handler(MessageHandler(filters.PHOTO, self.receipts.handle_photo))
        
        # Здоровье
        app.add_handler(CommandHandler("health", self._route_health_command))
        
        # Настройки
        app.add_handler(CommandHandler("mode", self.settings.set_mode))
        app.add_handler(CommandHandler("settings", self.settings.settings))
        app.add_handler(CommandHandler("advice", self.settings.toggle_advice))
        
        # Напоминания
        app.add_handler(CommandHandler("remind", self.reminders.remind_add))
        
        # Экспорт и отчеты
        app.add_handler(CommandHandler("export", self.export.export_command))
        app.add_handler(CommandHandler("report", self.export.report_command))
        
        # Microsoft интеграция
        app.add_handler(CommandHandler("ms", self.microsoft.ms_command))
        
        # Обработка документов
        app.add_handler(MessageHandler(filters.Document.ALL, self.projects.handle_document))
        
        # Текстовые сообщения (дневник здоровья)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
    
    async def _route_project_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Роутинг команд проектов"""
        if not context.args:
            await self.projects.project_list(update, context)
            return
        
        subcommand = context.args[0].lower()
        context.args = context.args[1:]  # Убираем подкоманду
        
        if subcommand == 'list':
            await self.projects.project_list(update, context)
        elif subcommand == 'add':
            await self.projects.project_add(update, context)
        elif subcommand == 'info':
            await self.projects.project_info(update, context)
        elif subcommand == 'done':
            await self.projects.project_done(update, context)
        elif subcommand == 'delete':
            await self.projects.project_delete(update, context)
        else:
            await update.message.reply_text(
                "❌ Неизвестная подкоманда.\n\n"
                "Доступные: `list`, `add`, `info`, `done`, `delete`",
                parse_mode='Markdown'
            )
    
    async def _route_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Роутинг команд задач"""
        if not context.args:
            await self.tasks.task_list(update, context)
            return
        
        subcommand = context.args[0].lower()
        context.args = context.args[1:]
        
        if subcommand == 'list':
            await self.tasks.task_list(update, context)
        elif subcommand == 'add':
            await self.tasks.task_add(update, context)
        elif subcommand == 'done':
            await self.tasks.task_done(update, context)
        elif subcommand == 'priority':
            await self.tasks.task_priority(update, context)
        elif subcommand == 'all':
            await self.tasks.task_all(update, context)
        else:
            await update.message.reply_text(
                "❌ Неизвестная подкоманда.\n\n"
                "Доступные: `list`, `add`, `done`, `priority`, `all`",
                parse_mode='Markdown'
            )
    
    async def _route_receipt_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Роутинг команд чеков"""
        if not context.args:
            await update.message.reply_text(
                "🧾 **КОМАНДЫ ЧЕКОВ:**\n\n"
                "• Отправь фото чека - автоанализ\n"
                "• `/receipt history` - история покупок\n"
                "• `/receipt stats` - статистика",
                parse_mode='Markdown'
            )
            return
        
        subcommand = context.args[0].lower()
        
        if subcommand == 'history':
            await self.receipts.receipt_history(update, context)
        elif subcommand == 'stats':
            await self.receipts.receipt_stats(update, context)
        else:
            await update.message.reply_text("❌ Неизвестная подкоманда")
    
    async def _route_health_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Роутинг команд здоровья"""
        if not context.args:
            await update.message.reply_text(
                "💪 **ДНЕВНИК ЗДОРОВЬЯ:**\n\n"
                "Просто напиши что съел или сделал:\n"
                "• _Съел яблоко_\n"
                "• _Пробежал 5 км_\n"
                "• _Спал 8 часов_\n\n"
                "Команды:\n"
                "• `/health report` - отчет за день\n"
                "• `/health week` - отчет за неделю",
                parse_mode='Markdown'
            )
            return
        
        subcommand = context.args[0].lower()
        
        if subcommand == 'report':
            await self.health.health_report(update, context)
        elif subcommand == 'week':
            await self.health.health_week(update, context)
        else:
            await update.message.reply_text("❌ Неизвестная подкоманда")


async def post_init(application: Application):
    """Инициализация после запуска"""
    bot = application.bot_data.get('bot_instance')
    if bot:
        bot.application = application
        await bot.start_notification_service()


async def post_shutdown(application: Application):
    """Очистка при остановке"""
    bot = application.bot_data.get('bot_instance')
    if bot:
        await bot.stop_notification_service()


def main():
    """Запуск бота"""
    # Проверка конфигурации
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(f"❌ {error}")
        return
    
    # Создание приложения
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()
    
    # Создание и настройка бота
    bot = PersonalAssistantBot(app)
    bot.setup_handlers(app)
    
    # Сохранить экземпляр бота
    app.bot_data['bot_instance'] = bot
    
    # Запуск
    logger.info("🚀 Personal Assistant Bot запущен!")
    logger.info("📋 Команды: /start /help /project /task /receipt /health /remind /export /report /ms")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
