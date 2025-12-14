"""
Обработчик команд для проектов
"""

from telegram import Update
from telegram.ext import ContextTypes

from services.supabase_service import SupabaseService
from services.storage_service import StorageService


class ProjectsHandler:
    """Обработчик команд проектов"""
    
    def __init__(self):
        self.db = SupabaseService()
        self.storage = StorageService()
    
    async def project_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Список проектов /project list"""
        user_id = str(update.effective_user.id)
        
        projects = await self.db.get_user_projects(user_id)
        
        if not projects:
            await update.message.reply_text(
                "📂 У тебя пока нет проектов.\n\n"
                "Создай первый: `/project add Название проекта`",
                parse_mode='Markdown'
            )
            return
        
        message = "📂 **ТВОИ ПРОЕКТЫ:**\n\n"
        
        for i, project in enumerate(projects, 1):
            status_emoji = {
                'active': '🟢',
                'done': '✅',
                'archived': '📦'
            }.get(project['status'], '⚪')
            
            message += f"{i}. {status_emoji} **{project['project_name']}**\n"
            
            if project.get('description'):
                message += f"   └ {project['description'][:50]}...\n"
            
            files_count = project.get('files_count', 0)
            tasks_count = project.get('tasks_count', 0)
            
            message += f"   📄 Файлов: {files_count} | 📋 Задач: {tasks_count}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def project_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Создать проект /project add [название]"""
        user_id = str(update.effective_user.id)
        
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи название проекта:\n"
                "`/project add Название проекта`",
                parse_mode='Markdown'
            )
            return
        
        project_name = ' '.join(context.args)
        
        # Проверить лимиты
        projects_count = await self.db.count_user_projects(user_id)
        if projects_count >= 100:
            await update.message.reply_text(
                "❌ Достигнут лимит проектов (100).\n"
                "Удали или заархивируй старые проекты."
            )
            return
        
        # Создать проект
        project = await self.db.create_project(
            user_id=user_id,
            project_name=project_name
        )
        
        message = f"✅ Проект **{project_name}** создан!\n\n"
        message += "Что дальше:\n"
        message += "• Загрузи файлы - просто отправь документ\n"
        message += "• Добавь задачи: `/task add Описание`\n"
        message += f"• Посмотри детали: `/project info {project['id'][:8]}`"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def project_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Информация о проекте /project info [id]"""
        user_id = str(update.effective_user.id)
        
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи ID проекта:\n"
                "`/project info [ID]`\n\n"
                "Посмотри ID в списке: `/project list`",
                parse_mode='Markdown'
            )
            return
        
        project_id = context.args[0]
        project = await self.db.get_project_by_id(project_id, user_id)
        
        if not project:
            await update.message.reply_text("❌ Проект не найден")
            return
        
        message = f"📂 **{project['project_name']}**\n\n"
        
        if project.get('description'):
            message += f"📝 {project['description']}\n\n"
        
        status_text = {
            'active': '🟢 Активен',
            'done': '✅ Завершен',
            'archived': '📦 В архиве'
        }.get(project['status'], project['status'])
        
        message += f"Статус: {status_text}\n"
        message += f"Создан: {project['created_at'][:10]}\n"
        
        if project.get('deadline'):
            message += f"Дедлайн: {project['deadline'][:10]}\n"
        
        # Файлы
        files = await self.db.get_project_files(project['id'])
        if files:
            message += f"\n📄 **Файлы ({len(files)}):**\n"
            for f in files[:5]:
                message += f"• {f['file_name']}\n"
            if len(files) > 5:
                message += f"... и еще {len(files) - 5}\n"
        
        # Задачи
        tasks = await self.db.get_project_tasks(project['id'])
        if tasks:
            pending = sum(1 for t in tasks if t['status'] == 'pending')
            message += f"\n📋 **Задачи:** {pending} активных из {len(tasks)}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def project_done(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Завершить проект /project done [id]"""
        user_id = str(update.effective_user.id)
        
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи ID проекта:\n`/project done [ID]`",
                parse_mode='Markdown'
            )
            return
        
        project_id = context.args[0]
        success = await self.db.update_project_status(project_id, user_id, 'done')
        
        if success:
            await update.message.reply_text("✅ Проект завершен!")
        else:
            await update.message.reply_text("❌ Проект не найден")
    
    async def project_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Удалить проект /project delete [id]"""
        user_id = str(update.effective_user.id)
        
        if not context.args:
            await update.message.reply_text(
                "❌ Укажи ID проекта:\n`/project delete [ID]`",
                parse_mode='Markdown'
            )
            return
        
        project_id = context.args[0]
        success = await self.db.delete_project(project_id, user_id)
        
        if success:
            await update.message.reply_text("🗑️ Проект удален")
        else:
            await update.message.reply_text("❌ Проект не найден")
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка загруженного документа"""
        user_id = str(update.effective_user.id)
        document = update.message.document
        
        # Проверка размера
        if document.file_size > 20 * 1024 * 1024:  # 20 MB
            await update.message.reply_text("❌ Файл слишком большой (макс. 20 МБ)")
            return
        
        # Скачать файл
        file = await document.get_file()
        file_bytes = await file.download_as_bytearray()
        
        # Загрузить в Storage
        file_url = await self.storage.upload_file(
            bucket='projects',
            path=f"{user_id}/{document.file_name}",
            file_data=bytes(file_bytes),
            content_type=document.mime_type
        )
        
        # Сохранить в БД (без привязки к проекту пока)
        await self.db.save_project_file(
            project_id=None,
            file_name=document.file_name,
            file_url=file_url,
            file_size=document.file_size,
            file_type=document.mime_type,
            user_id=user_id
        )
        
        await update.message.reply_text(
            f"✅ Файл **{document.file_name}** загружен!\n\n"
            "Чтобы привязать к проекту, создай проект: `/project add Название`",
            parse_mode='Markdown'
        )
