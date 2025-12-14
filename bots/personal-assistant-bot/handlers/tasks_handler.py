"""
Обработчик команд для задач
"""

from telegram import Update
from telegram.ext import ContextTypes

from services.supabase_service import SupabaseService


class TasksHandler:
    """Обработчик команд задач"""
    
    def __init__(self):
        self.db = SupabaseService()
    
    async def task_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Список активных задач /task list"""
        user_id = str(update.effective_user.id)
        
        # Получить только активные задачи
        tasks = await self.db.get_user_tasks(user_id, status='pending')
        
        if not tasks:
            await update.message.reply_text(
                "✅ У тебя нет активных задач!\n\n"
                "Добавь новую: `/task add Описание задачи`",
                parse_mode='Markdown'
            )
            return
        
        message = "📋 **АКТИВНЫЕ ЗАДАЧИ:**\n\n"
        
        for i, task in enumerate(tasks, 1):
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(task['priority'], '⚪')
            
            message += f"{i}. {priority_emoji} {task['task_description']}\n"
            
            if task.get('due_date'):
                message += f"   └ Срок: {task['due_date'][:10]}\n"
            
            if task.get('project_name'):
                message += f"   └ Проект: {task['project_name']}\n"
        
        message += "\n_Отметить выполненной:_ `/task done [номер]`"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def task_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Добавить задачу /task add [описание]"""
        user_id = str(update.effective_user.id)
        
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи описание задачи:\n"
                "`/task add Купить молоко`",
                parse_mode='Markdown'
            )
            return
        
        task_description = ' '.join(context.args)
        
        # Проверить лимиты
        tasks_count = await self.db.count_user_tasks(user_id)
        if tasks_count >= 1000:
            await update.message.reply_text(
                "❌ Достигнут лимит задач (1000).\n"
                "Заверши или удали старые задачи."
            )
            return
        
        # Определить приоритет из текста
        priority = 'medium'
        text_lower = task_description.lower()
        if any(word in text_lower for word in ['срочно', 'важно', 'asap', 'критично']):
            priority = 'high'
        elif any(word in text_lower for word in ['потом', 'когда-нибудь', 'не срочно']):
            priority = 'low'
        
        # Создать задачу
        task = await self.db.create_task(
            user_id=user_id,
            task_description=task_description,
            priority=priority
        )
        
        priority_text = {
            'high': '🔴 Высокий',
            'medium': '🟡 Средний',
            'low': '🟢 Низкий'
        }.get(priority, priority)
        
        await update.message.reply_text(
            f"✅ Задача добавлена!\n\n"
            f"📋 {task_description}\n"
            f"Приоритет: {priority_text}\n\n"
            f"_Отметить выполненной:_ `/task done 1`",
            parse_mode='Markdown'
        )
    
    async def task_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отметить задачу выполненной /task done [номер]"""
        user_id = str(update.effective_user.id)
        
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи номер задачи:\n"
                "`/task done 1`\n\n"
                "Посмотри номера: `/task list`",
                parse_mode='Markdown'
            )
            return
        
        try:
            task_number = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Укажи номер задачи числом")
            return
        
        # Получить задачи и найти по номеру
        tasks = await self.db.get_user_tasks(user_id, status='pending')
        
        if task_number < 1 or task_number > len(tasks):
            await update.message.reply_text(
                f"❌ Задача #{task_number} не найдена\n"
                f"Всего активных задач: {len(tasks)}"
            )
            return
        
        task = tasks[task_number - 1]
        
        # Обновить статус
        await self.db.update_task_status(task['id'], 'done')
        
        await update.message.reply_text(
            f"✅ Задача выполнена!\n\n"
            f"~~{task['task_description']}~~",
            parse_mode='Markdown'
        )
    
    async def task_priority(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Изменить приоритет /task priority [номер] [приоритет]"""
        user_id = str(update.effective_user.id)
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Укажи номер и приоритет:\n"
                "`/task priority 1 high`\n\n"
                "Приоритеты: `high`, `medium`, `low`",
                parse_mode='Markdown'
            )
            return
        
        try:
            task_number = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Укажи номер задачи числом")
            return
        
        priority = context.args[1].lower()
        if priority not in ['high', 'medium', 'low']:
            await update.message.reply_text("❌ Приоритет: `high`, `medium` или `low`", parse_mode='Markdown')
            return
        
        # Получить задачи
        tasks = await self.db.get_user_tasks(user_id, status='pending')
        
        if task_number < 1 or task_number > len(tasks):
            await update.message.reply_text(f"❌ Задача #{task_number} не найдена")
            return
        
        task = tasks[task_number - 1]
        
        # Обновить приоритет
        await self.db.update_task_priority(task['id'], priority)
        
        priority_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(priority)
        
        await update.message.reply_text(
            f"✅ Приоритет изменен на {priority_emoji} {priority}"
        )
    
    async def task_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать все задачи (включая выполненные) /task all"""
        user_id = str(update.effective_user.id)
        
        tasks = await self.db.get_user_tasks(user_id, status=None)  # Все задачи
        
        if not tasks:
            await update.message.reply_text("📋 У тебя нет задач")
            return
        
        pending = [t for t in tasks if t['status'] == 'pending']
        done = [t for t in tasks if t['status'] == 'done']
        
        message = f"📋 **ВСЕ ЗАДАЧИ** ({len(pending)} активных, {len(done)} выполненных)\n\n"
        
        if pending:
            message += "**Активные:**\n"
            for i, task in enumerate(pending, 1):
                message += f"{i}. {task['task_description']}\n"
        
        if done:
            message += "\n**Выполненные (последние 5):**\n"
            for task in done[:5]:
                message += f"✅ ~~{task['task_description']}~~\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
