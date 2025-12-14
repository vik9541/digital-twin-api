"""
Единая точка входа — обрабатывает любые текстовые сообщения.
Бот работает как "Единое окно": пользователь пишет обычным текстом,
бот сам понимает что нужно и действует.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from .dispatcher import dispatch_message, Intent, ParsedIntent

logger = logging.getLogger(__name__)


class UnifiedHandler:
    """
    Единый обработчик всех текстовых сообщений.
    Определяет интент и делегирует в нужный handler.
    """
    
    def __init__(self, tasks_handler, projects_handler, health_handler, 
                 reminders_handler, receipts_handler, export_handler):
        """
        Args:
            tasks_handler: TasksHandler instance
            projects_handler: ProjectsHandler instance  
            health_handler: HealthHandler instance
            reminders_handler: RemindersHandler instance
            receipts_handler: ReceiptsHandler instance
            export_handler: ExportHandler instance
        """
        self.tasks = tasks_handler
        self.projects = projects_handler
        self.health = health_handler
        self.reminders = reminders_handler
        self.receipts = receipts_handler
        self.reports = export_handler
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Главная точка входа для всех текстовых сообщений.
        Определяет интент и вызывает соответствующий freeform-метод.
        """
        text = update.message.text or ""
        user_id = str(update.effective_user.id)
        
        # Определяем интент
        parsed = dispatch_message(text, has_photo=False)
        
        logger.info(f"User {user_id}: '{text[:50]}...' → {parsed.intent.value} (conf={parsed.confidence:.2f})")
        
        # Роутинг по интенту
        try:
            if parsed.intent == Intent.TASK:
                await self._handle_task(update, context, parsed)
            
            elif parsed.intent == Intent.PROJECT:
                await self._handle_project(update, context, parsed)
            
            elif parsed.intent == Intent.HEALTH:
                await self._handle_health(update, context, parsed)
            
            elif parsed.intent == Intent.REMINDER:
                await self._handle_reminder(update, context, parsed)
            
            elif parsed.intent == Intent.REPORT:
                await self._handle_report(update, context, parsed)
            
            elif parsed.intent == Intent.SMALL_TALK:
                await self._handle_small_talk(update, context, parsed)
            
            else:
                # UNKNOWN — пробуем как здоровье или даём подсказку
                handled = await self.health.handle_health_message(update, context)
                if not handled:
                    await update.message.reply_text(
                        "🤔 Не совсем понял. Попробуй:\n"
                        "• \"Запиши задачу: ...\"\n"
                        "• \"Создай проект ...\"\n"
                        "• \"Напомни через 30 мин ...\""
                    )
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await update.message.reply_text("❌ Что-то пошло не так. Попробуй ещё раз.")
    
    async def _handle_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE, parsed: ParsedIntent):
        """Обработка задачи"""
        user_id = str(update.effective_user.id)
        payload = parsed.payload
        
        description = payload.get('description', parsed.original_text)
        deadline = payload.get('deadline')
        
        # Создаём задачу через сервис
        await self.tasks.db.create_task(
            user_id=user_id,
            task_description=description,
            priority='medium'
        )
        
        # Формируем короткий ответ
        response = f"✅ Задача добавлена: \"{description[:50]}{'...' if len(description) > 50 else ''}\""
        if deadline:
            response += f" (дедлайн: {deadline})"
        
        await update.message.reply_text(response)
    
    async def _handle_project(self, update: Update, context: ContextTypes.DEFAULT_TYPE, parsed: ParsedIntent):
        """Обработка проекта"""
        user_id = str(update.effective_user.id)
        payload = parsed.payload
        action = payload.get('action', 'info')
        name = payload.get('name')
        
        if action == 'create':
            if not name:
                await update.message.reply_text("📂 Как назвать проект?")
                return
            
            await self.projects.db.create_project(user_id=user_id, project_name=name)
            await update.message.reply_text(
                f"📂 Проект \"{name}\" создан.\n"
                "Можешь прислать файлы или добавить задачи."
            )
        
        elif action == 'list':
            projects = await self.projects.db.get_user_projects(user_id)
            if not projects:
                await update.message.reply_text("📂 У тебя пока нет проектов.")
            else:
                lines = ["📂 Твои проекты:"]
                for p in projects[:5]:
                    status = "🟢" if p['status'] == 'active' else "✅"
                    lines.append(f"{status} {p['project_name']}")
                await update.message.reply_text("\n".join(lines))
        
        else:
            # Показываем список
            projects = await self.projects.db.get_user_projects(user_id)
            count = len(projects) if projects else 0
            await update.message.reply_text(f"📂 У тебя {count} проект(ов). Скажи \"мои проекты\" для списка.")
    
    async def _handle_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE, parsed: ParsedIntent):
        """Обработка записи в дневник здоровья"""
        user_id = str(update.effective_user.id)
        payload = parsed.payload
        
        entry_type = payload.get('entry_type', 'other')
        description = payload.get('description', parsed.original_text)
        time_str = payload.get('time')
        
        # Сохраняем запись
        await self.health.db.save_health_entry(
            user_id=user_id,
            entry_type=entry_type,
            description=description,
            data={'time': time_str} if time_str else {}
        )
        
        # Короткий ответ
        emoji_map = {
            'food': '🍽️',
            'habit': '🚬',
            'activity': '🏃',
            'sleep': '😴',
            'measurement': '📏',
            'other': '📝'
        }
        
        type_names = {
            'food': 'питание',
            'habit': 'привычка',
            'activity': 'активность',
            'sleep': 'сон',
            'measurement': 'измерение',
            'other': 'запись'
        }
        
        emoji = emoji_map.get(entry_type, '📝')
        type_name = type_names.get(entry_type, 'запись')
        
        response = f"{emoji} Записано: {type_name}"
        if time_str:
            response += f" в {time_str}"
        
        await update.message.reply_text(response)
    
    async def _handle_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE, parsed: ParsedIntent):
        """Обработка напоминания"""
        payload = parsed.payload
        
        reminder_text = payload.get('text', 'Напоминание')
        time_str = payload.get('time_str')
        
        if not time_str:
            await update.message.reply_text(
                "⏰ Когда напомнить? Например:\n"
                "• через 30 минут\n"
                "• в 15:00"
            )
            return
        
        # Используем существующий метод
        if self.reminders.notifications:
            user_id = str(update.effective_user.id)
            remind_time = self.reminders.notifications.parse_reminder_time(time_str + " " + reminder_text)
            
            if remind_time:
                self.reminders.notifications.add_reminder(
                    user_id=user_id,
                    text=reminder_text,
                    remind_at=remind_time
                )
                await update.message.reply_text(f"⏰ Ок, напомню {time_str}.")
            else:
                await update.message.reply_text("⏰ Не понял время. Попробуй: \"через 30 минут\" или \"в 15:00\"")
        else:
            await update.message.reply_text("⏰ Сервис напоминаний не настроен.")
    
    async def _handle_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, parsed: ParsedIntent):
        """Обработка запроса отчёта"""
        user_id = str(update.effective_user.id)
        payload = parsed.payload
        
        report_type = payload.get('report_type', 'general')
        period = payload.get('period', 'day')
        
        period_days = {'day': 1, 'week': 7, 'month': 30}.get(period, 7)
        period_name = {'day': 'сегодня', 'week': 'неделю', 'month': 'месяц'}.get(period, 'неделю')
        
        if report_type == 'health':
            entries = await self.health.db.get_health_entries(user_id, days=period_days)
            count = len(entries) if entries else 0
            
            # Группируем по типам
            by_type = {}
            for e in (entries or []):
                t = e.get('entry_type', 'other')
                by_type[t] = by_type.get(t, 0) + 1
            
            lines = [f"📊 Здоровье за {period_name}:"]
            if by_type:
                type_emoji = {'food': '🍽️', 'habit': '🚬', 'activity': '🏃', 'sleep': '😴'}
                for t, c in by_type.items():
                    emoji = type_emoji.get(t, '📝')
                    lines.append(f"{emoji} {t}: {c}")
            else:
                lines.append("Записей нет")
            
            await update.message.reply_text("\n".join(lines))
        
        elif report_type == 'expenses':
            receipts = await self.receipts.db.get_user_receipts(user_id, limit=100)
            total = sum(r.get('total_sum', 0) or 0 for r in (receipts or []))
            count = len(receipts) if receipts else 0
            
            await update.message.reply_text(
                f"📊 Расходы за {period_name}:\n"
                f"🧾 Чеков: {count}\n"
                f"💰 Сумма: {total:.0f} ₽"
            )
        
        elif report_type == 'tasks':
            tasks = await self.tasks.db.get_user_tasks(user_id, status=None)
            pending = len([t for t in (tasks or []) if t.get('status') == 'pending'])
            done = len([t for t in (tasks or []) if t.get('status') == 'done'])
            
            await update.message.reply_text(
                f"📊 Задачи:\n"
                f"📋 Активных: {pending}\n"
                f"✅ Выполнено: {done}"
            )
        
        else:
            # Общий отчёт
            await update.message.reply_text(
                "📊 Какой отчёт нужен?\n"
                "• \"отчёт по здоровью за неделю\"\n"
                "• \"отчёт по расходам\"\n"
                "• \"отчёт по задачам\""
            )
    
    async def _handle_small_talk(self, update: Update, context: ContextTypes.DEFAULT_TYPE, parsed: ParsedIntent):
        """Обработка small talk"""
        text_lower = parsed.original_text.lower()
        
        if any(w in text_lower for w in ['привет', 'здравствуй', 'hi', 'hello']):
            await update.message.reply_text("👋 Привет! Что нужно сделать?")
        
        elif any(w in text_lower for w in ['спасибо', 'благодарю', 'thanks']):
            await update.message.reply_text("👍")
        
        elif any(w in text_lower for w in ['пока', 'до свидания', 'bye']):
            await update.message.reply_text("👋 Пока!")
        
        elif any(w in text_lower for w in ['как дела', 'что умеешь']):
            await update.message.reply_text(
                "Я помогу с:\n"
                "• Задачами\n"
                "• Проектами\n"
                "• Чеками (пришли фото)\n"
                "• Здоровьем\n"
                "• Напоминаниями"
            )
        
        else:
            await update.message.reply_text("👍 Ок")


# Создаётся в main.py после инициализации всех handlers
unified_handler = None


def create_unified_handler(tasks, projects, health, reminders, receipts, reports) -> UnifiedHandler:
    """Фабрика для создания UnifiedHandler"""
    global unified_handler
    unified_handler = UnifiedHandler(tasks, projects, health, reminders, receipts, reports)
    return unified_handler
