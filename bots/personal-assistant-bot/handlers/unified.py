"""
Единая точка входа — обрабатывает любые текстовые сообщения.
Бот работает как "Единое окно": пользователь пишет обычным текстом,
бот сам понимает что нужно и действует.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from services.intent_classifier import get_classifier, Intent, ClassificationResult

logger = logging.getLogger(__name__)


class UnifiedHandler:
    """
    Единый обработчик всех текстовых сообщений.
    Определяет интент и делегирует в нужный handler.
    """
    
    def __init__(self, tasks_handler, projects_handler, health_handler, 
                 reminders_handler, receipts_handler, export_handler, 
                 contacts_handler=None, work_tracker_handler=None):
        """
        Args:
            tasks_handler: TasksHandler instance
            projects_handler: ProjectsHandler instance  
            health_handler: HealthHandler instance
            reminders_handler: RemindersHandler instance
            receipts_handler: ReceiptsHandler instance
            export_handler: ExportHandler instance
            contacts_handler: ContactsHandler instance
            work_tracker_handler: WorkTrackerHandler instance
        """
        self.tasks = tasks_handler
        self.projects = projects_handler
        self.health = health_handler
        self.reminders = reminders_handler
        self.receipts = receipts_handler
        self.reports = export_handler
        self.contacts = contacts_handler
        self.work_tracker = work_tracker_handler
        
        # Новый классификатор интентов
        self.classifier = get_classifier()
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Главная точка входа для всех текстовых сообщений.
        Определяет интент и вызывает соответствующий freeform-метод.
        """
        text = update.message.text or ""
        user_id = str(update.effective_user.id)
        
        # Классифицируем интент через новый классификатор
        result = self.classifier.classify(text)
        
        logger.info(f"User {user_id}: '{text[:50]}...' → {result.intent.value} (conf={result.confidence:.2f})")
        
        # Роутинг по интенту
        try:
            # Рабочее время
            if result.intent in [Intent.WORK_ARRIVAL, Intent.WORK_DEPARTURE, 
                                  Intent.WORK_BREAK_START, Intent.WORK_BREAK_END,
                                  Intent.WORK_STATUS, Intent.WORK_REPORT]:
                await self._handle_work(update, context, result)
            
            # Контакты
            elif result.intent in [Intent.CONTACT_ADD, Intent.CONTACT_SEARCH,
                                    Intent.CONTACT_INFO, Intent.CONTACT_LIST,
                                    Intent.CONTACT_DELETE, Intent.CONTACT_INTERACTION]:
                await self._handle_contact(update, context, result)
            
            # Задачи
            elif result.intent in [Intent.TASK_ADD, Intent.TASK_LIST,
                                    Intent.TASK_COMPLETE, Intent.TASK_DELETE]:
                await self._handle_task(update, context, result)
            
            # Здоровье
            elif result.intent in [Intent.HEALTH_LOG, Intent.HEALTH_STATUS]:
                await self._handle_health(update, context, result)
            
            # Чеки
            elif result.intent in [Intent.RECEIPT_ADD, Intent.RECEIPT_LIST]:
                await self._handle_receipt(update, context, result)
            
            # Общение
            elif result.intent == Intent.GREETING:
                await self._handle_greeting(update, context)
            
            elif result.intent == Intent.THANKS:
                await update.message.reply_text("👍 Всегда рад помочь!")
            
            elif result.intent == Intent.HELP:
                await self._handle_help(update, context)
            
            else:
                # UNKNOWN — пробуем как здоровье или даём подсказку
                handled = await self.health.handle_health_message(update, context)
                if not handled:
                    await update.message.reply_text(
                        "🤔 Не совсем понял. Попробуй:\n"
                        "• \"Пришёл на работу\"\n"
                        "• \"Добавь контакт Иван 89991234567\"\n"
                        "• \"Запиши задачу: ...\"\n"
                        "• \"Напомни через 30 мин ...\""
                    )
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text("❌ Что-то пошло не так. Попробуй ещё раз.")
    
    async def _handle_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: ClassificationResult):
        """Обработка задачи"""
        user_id = str(update.effective_user.id)
        
        if result.intent == Intent.TASK_ADD:
            # Извлекаем описание задачи из текста
            description = result.raw_text
            # Убираем ключевые слова
            for word in ['добавь задачу', 'запиши задачу', 'создай задачу', 'нужно сделать', 'не забыть']:
                description = description.lower().replace(word, '').strip()
            
            if not description:
                description = result.raw_text
            
            # Создаём задачу через сервис
            await self.tasks.db.create_task(
                user_id=user_id,
                task_description=description.strip(),
                priority='medium'
            )
            
            await update.message.reply_text(f"✅ Задача добавлена: \"{description[:50]}{'...' if len(description) > 50 else ''}\"")
        
        elif result.intent == Intent.TASK_LIST:
            tasks = await self.tasks.db.get_user_tasks(user_id, status='pending')
            if not tasks:
                await update.message.reply_text("📋 У тебя нет активных задач")
            else:
                lines = ["📋 **Твои задачи:**"]
                for i, t in enumerate(tasks[:10], 1):
                    lines.append(f"{i}. {t.get('task_description', '')[:50]}")
                await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
        
        else:
            await update.message.reply_text("📋 Скажи \"мои задачи\" или \"добавь задачу: ...\"")
    
    async def _handle_work(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: ClassificationResult):
        """Обработка рабочего времени"""
        if not self.work_tracker:
            await update.message.reply_text("❌ Сервис учёта рабочего времени не настроен")
            return
        
        user_id = str(update.effective_user.id)
        response = await self.work_tracker.handle_natural(user_id, result.raw_text)
        
        if response:
            await update.message.reply_text(response, parse_mode='Markdown')
        else:
            await update.message.reply_text("🤔 Не понял команду. Попробуй: \"пришёл на работу\" или \"ушёл с работы\"")
    
    async def _handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: ClassificationResult):
        """Обработка контактов"""
        if not self.contacts:
            await update.message.reply_text("❌ Сервис контактов не настроен")
            return
        
        user_id = str(update.effective_user.id)
        
        if result.intent == Intent.CONTACT_ADD:
            response = await self.contacts.add_contact_natural(user_id, result.raw_text)
        elif result.intent == Intent.CONTACT_LIST:
            contacts = self.contacts.db.get_contacts(user_id)
            if not contacts:
                response = "📇 У тебя пока нет контактов"
            else:
                lines = ["📇 **Твои контакты:**"]
                for c in contacts[:10]:
                    name = c.get('name', 'Без имени')
                    phone = c.get('phone', '')
                    fav = "⭐ " if c.get('is_favorite') else ""
                    lines.append(f"{fav}{name}" + (f" — {phone}" if phone else ""))
                response = "\n".join(lines)
        else:
            response = await self.contacts.search_contact_natural(user_id, result.raw_text)
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def _handle_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: ClassificationResult):
        """Обработка записи в дневник здоровья"""
        # Используем существующий обработчик
        await self.health.handle_health_message(update, context)
    
    async def _handle_receipt(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: ClassificationResult):
        """Обработка чеков"""
        user_id = str(update.effective_user.id)
        
        if result.intent == Intent.RECEIPT_LIST:
            receipts = await self.receipts.db.get_user_receipts(user_id, limit=10)
            if not receipts:
                await update.message.reply_text("🧾 У тебя пока нет чеков")
            else:
                total = sum(r.get('total_sum', 0) or 0 for r in receipts)
                lines = [f"🧾 **Последние чеки:** (всего {total:.0f} ₽)"]
                for r in receipts[:5]:
                    shop = r.get('shop_name', 'Магазин')
                    amount = r.get('total_sum', 0) or 0
                    lines.append(f"• {shop}: {amount:.0f} ₽")
                await update.message.reply_text("\n".join(lines), parse_mode='Markdown')
        else:
            # Пробуем извлечь сумму
            amount = result.extracted_data.get('amount')
            if amount:
                await update.message.reply_text(f"🧾 Для добавления чека отправь фото чека или используй /receipt")
            else:
                await update.message.reply_text("🧾 Отправь фото чека для распознавания или скажи \"мои чеки\"")
    
    async def _handle_greeting(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Приветствие"""
        await update.message.reply_text(
            "👋 Привет! Я твой персональный ассистент.\n\n"
            "Что я умею:\n"
            "• 🏢 \"Пришёл на работу\" / \"Ушёл с работы\"\n"
            "• 📇 \"Добавь контакт Иван 89991234567\"\n"
            "• 📋 \"Добавь задачу: ...\"\n"
            "• ⏰ \"Напомни через 30 мин ...\"\n"
            "• 🧾 Отправь фото чека\n\n"
            "Просто пиши обычным текстом!"
        )
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Помощь"""
        await update.message.reply_text(
            "📖 **Мои команды:**\n\n"
            "**Рабочее время:**\n"
            "• Пришёл на работу\n"
            "• Ушёл с работы\n"
            "• /work статус\n\n"
            "**Контакты:**\n"
            "• Добавь контакт Иван 89991234567\n"
            "• Найди контакт Иван\n"
            "• /contact list\n\n"
            "**Задачи:**\n"
            "• Добавь задачу: купить молоко\n"
            "• Мои задачи\n\n"
            "**Чеки:**\n"
            "• Отправь фото чека\n"
            "• Мои чеки\n\n"
            "**Здоровье:**\n"
            "• Съел яблоко\n"
            "• Выкурил сигарету\n",
            parse_mode='Markdown'
        )
    
# Создаётся в main.py после инициализации всех handlers
unified_handler = None


def create_unified_handler(tasks, projects, health, reminders, receipts, reports, 
                           contacts=None, work_tracker=None) -> UnifiedHandler:
    """Фабрика для создания UnifiedHandler"""
    global unified_handler
    unified_handler = UnifiedHandler(
        tasks, projects, health, reminders, receipts, reports, 
        contacts, work_tracker
    )
    return unified_handler
