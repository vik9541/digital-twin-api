"""
Обработчик интеграции с Microsoft Graph
Контакты, календарь, почта
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from services.microsoft_graph import MicrosoftGraphService, format_contact_for_graph
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class MicrosoftHandler:
    """Обработчик команд Microsoft"""
    
    def __init__(self):
        self.db = SupabaseService()
        self._graph_clients = {}  # user_id -> MicrosoftGraphService
    
    def _get_client(self, user_id: str) -> MicrosoftGraphService:
        """Получить клиент Graph API для пользователя"""
        return self._graph_clients.get(user_id)
    
    async def ms_auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Авторизация в Microsoft
        /ms auth TOKEN
        """
        if not context.args:
            await update.message.reply_text(
                "🔐 **АВТОРИЗАЦИЯ MICROSOFT**\n\n"
                "1. Получи токен на [Graph Explorer](https://developer.microsoft.com/graph/graph-explorer)\n"
                "2. Отправь: `/ms auth ТВОЙ_ТОКЕН`\n\n"
                "Токен нужен для:\n"
                "• Синхронизации контактов\n"
                "• Работы с календарем\n"
                "• Проверки почты",
                parse_mode='Markdown'
            )
            return
        
        token = context.args[0]
        user_id = str(update.effective_user.id)
        
        # Проверка токена
        client = MicrosoftGraphService(token)
        is_valid = await client.validate_token()
        
        if not is_valid:
            await update.message.reply_text("❌ Токен невалиден или истек")
            return
        
        # Сохранение клиента
        self._graph_clients[user_id] = client
        
        profile = await client.get_profile()
        name = profile.get('displayName', 'Unknown')
        email = profile.get('mail') or profile.get('userPrincipalName', '')
        
        await update.message.reply_text(
            f"✅ **Авторизация успешна!**\n\n"
            f"👤 {name}\n"
            f"📧 {email}\n\n"
            f"Доступные команды:\n"
            f"• `/ms contacts` - контакты\n"
            f"• `/ms calendar` - календарь\n"
            f"• `/ms mail` - почта",
            parse_mode='Markdown'
        )
    
    async def ms_contacts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Работа с контактами
        /ms contacts - список
        /ms contacts search QUERY - поиск
        """
        user_id = str(update.effective_user.id)
        client = self._get_client(user_id)
        
        if not client:
            await update.message.reply_text(
                "❌ Сначала авторизуйся: `/ms auth TOKEN`",
                parse_mode='Markdown'
            )
            return
        
        # Подкоманды
        if context.args and context.args[0] == 'contacts':
            context.args = context.args[1:]
        
        if context.args and context.args[0].lower() == 'search':
            # Поиск контактов
            query = ' '.join(context.args[1:]) if len(context.args) > 1 else ''
            
            if not query:
                await update.message.reply_text("❌ Укажи что искать: `/ms contacts search Имя`", parse_mode='Markdown')
                return
            
            contacts = await client.search_contacts(query)
            
            if not contacts:
                await update.message.reply_text(f"📭 Контакты не найдены: _{query}_", parse_mode='Markdown')
                return
            
            lines = [f"🔍 **НАЙДЕНО ({len(contacts)}):**\n"]
            for c in contacts[:10]:
                name = c.get('displayName', 'Без имени')
                email = c.get('emailAddresses', [{}])[0].get('address', '')
                phone = c.get('mobilePhone', '')
                
                lines.append(f"• **{name}**")
                if email:
                    lines.append(f"  📧 {email}")
                if phone:
                    lines.append(f"  📱 {phone}")
            
            await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
        
        else:
            # Список контактов
            contacts = await client.get_contacts(top=20)
            
            if not contacts:
                await update.message.reply_text("📭 Контакты не найдены")
                return
            
            lines = [f"📇 **КОНТАКТЫ (показано {len(contacts)}):**\n"]
            for c in contacts:
                name = c.get('displayName', 'Без имени')
                lines.append(f"• {name}")
            
            lines.append("\n🔍 Поиск: `/ms contacts search Имя`")
            
            await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
    
    async def ms_calendar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Работа с календарем
        /ms calendar - события на неделю
        """
        user_id = str(update.effective_user.id)
        client = self._get_client(user_id)
        
        if not client:
            await update.message.reply_text(
                "❌ Сначала авторизуйся: `/ms auth TOKEN`",
                parse_mode='Markdown'
            )
            return
        
        events = await client.get_calendar_events(days=7)
        
        if not events:
            await update.message.reply_text("📭 Нет событий на ближайшую неделю")
            return
        
        lines = ["📅 **СОБЫТИЯ НА НЕДЕЛЮ:**\n"]
        
        for event in events[:10]:
            subject = event.get('subject', 'Без названия')
            start = event.get('start', {}).get('dateTime', '')[:16].replace('T', ' ')
            
            lines.append(f"• **{subject}**")
            lines.append(f"  🕐 {start}")
        
        await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
    
    async def ms_mail(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Работа с почтой
        /ms mail - последние письма
        """
        user_id = str(update.effective_user.id)
        client = self._get_client(user_id)
        
        if not client:
            await update.message.reply_text(
                "❌ Сначала авторизуйся: `/ms auth TOKEN`",
                parse_mode='Markdown'
            )
            return
        
        # Непрочитанные
        unread = await client.get_unread_count()
        
        # Последние письма
        emails = await client.get_recent_emails(top=5)
        
        lines = [f"📧 **ПОЧТА** (непрочитанных: {unread})\n"]
        
        for email in emails:
            subject = email.get('subject', 'Без темы')[:40]
            sender = email.get('from', {}).get('emailAddress', {}).get('name', 'Unknown')
            is_read = email.get('isRead', True)
            
            read_marker = "📬" if not is_read else "📭"
            lines.append(f"{read_marker} **{subject}**")
            lines.append(f"   От: _{sender}_")
        
        await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
    
    async def ms_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Главный роутер команд /ms
        """
        if not context.args:
            await update.message.reply_text(
                "🔷 **MICROSOFT ИНТЕГРАЦИЯ**\n\n"
                "Команды:\n"
                "• `/ms auth TOKEN` - авторизация\n"
                "• `/ms contacts` - контакты\n"
                "• `/ms contacts search NAME` - поиск\n"
                "• `/ms calendar` - календарь\n"
                "• `/ms mail` - почта\n\n"
                "📝 [Получить токен](https://developer.microsoft.com/graph/graph-explorer)",
                parse_mode='Markdown'
            )
            return
        
        subcommand = context.args[0].lower()
        
        if subcommand == 'auth':
            await self.ms_auth(update, context)
        elif subcommand == 'contacts':
            await self.ms_contacts(update, context)
        elif subcommand == 'calendar':
            await self.ms_calendar(update, context)
        elif subcommand == 'mail':
            await self.ms_mail(update, context)
        else:
            await update.message.reply_text(f"❌ Неизвестная команда: {subcommand}")
