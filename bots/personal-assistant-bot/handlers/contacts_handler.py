"""
Обработчик команд для работы с контактами
"""

import logging
import re
from telegram import Update
from telegram.ext import ContextTypes

from services.supabase_service import SupabaseService
from models.contact import Contact
from utils.helpers import Helpers

logger = logging.getLogger(__name__)


class ContactsHandler:
    """Обработчик команд контактов"""
    
    def __init__(self):
        self.db = SupabaseService()
    
    async def contact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Главный роутер команд /contact
        /contact - список контактов
        /contact add Имя Телефон - добавить
        /contact search Запрос - поиск
        /contact delete ID - удалить
        /contact fav ID - в избранное
        """
        user_id = str(update.effective_user.id)
        
        if not context.args:
            await self._list_contacts(update, user_id)
            return
        
        subcommand = context.args[0].lower()
        args = context.args[1:]
        
        if subcommand == 'add':
            await self._add_contact(update, user_id, args)
        elif subcommand == 'search' or subcommand == 'find':
            await self._search_contacts(update, user_id, args)
        elif subcommand == 'delete' or subcommand == 'del':
            await self._delete_contact(update, user_id, args)
        elif subcommand == 'fav' or subcommand == 'favorite':
            await self._toggle_favorite(update, user_id, args)
        elif subcommand == 'info':
            await self._contact_info(update, user_id, args)
        elif subcommand == 'list':
            await self._list_contacts(update, user_id, category=' '.join(args) if args else None)
        else:
            # Возможно это поиск без подкоманды
            await self._search_contacts(update, user_id, context.args)
    
    async def _list_contacts(self, update: Update, user_id: str, category: str = None):
        """Показать список контактов"""
        contacts = await self.db.get_contacts(user_id, limit=30, category=category)
        
        if not contacts:
            await update.message.reply_text(
                "📭 **У тебя пока нет контактов**\n\n"
                "Добавь первый:\n"
                "`/contact add Имя 89991234567`\n\n"
                "Или просто напиши:\n"
                "_\"Добавь контакт Иван 89991234567\"_",
                parse_mode='Markdown'
            )
            return
        
        lines = ["📇 **КОНТАКТЫ**\n"]
        
        # Сначала избранные
        favorites = [c for c in contacts if c.get('is_favorite')]
        regular = [c for c in contacts if not c.get('is_favorite')]
        
        if favorites:
            lines.append("⭐ **Избранные:**")
            for c in favorites:
                phone = f" 📱 {c['phone']}" if c.get('phone') else ""
                lines.append(f"  • {c['display_name']}{phone}")
            lines.append("")
        
        if regular:
            lines.append("👤 **Все контакты:**")
            for c in regular[:20]:
                phone = f" 📱 {c['phone']}" if c.get('phone') else ""
                lines.append(f"  • {c['display_name']}{phone}")
        
        if len(contacts) > 20:
            lines.append(f"\n_...и ещё {len(contacts) - 20}_")
        
        lines.append("\n🔍 Поиск: `/contact search Имя`")
        lines.append("➕ Добавить: `/contact add Имя Телефон`")
        
        await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
    
    async def _add_contact(self, update: Update, user_id: str, args: list):
        """Добавить контакт"""
        if not args:
            await update.message.reply_text(
                "❌ Укажи имя контакта\n\n"
                "Примеры:\n"
                "`/contact add Иван`\n"
                "`/contact add Иван Петров 89991234567`\n"
                "`/contact add Мама 89991234567`",
                parse_mode='Markdown'
            )
            return
        
        # Парсим имя и телефон
        text = ' '.join(args)
        phone = None
        name = text
        
        # Ищем телефон в тексте
        phone_match = re.search(r'[\+]?[78]?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', text)
        if phone_match:
            phone = Helpers.clean_phone(phone_match.group())
            name = text.replace(phone_match.group(), '').strip()
        
        if not name:
            name = "Без имени"
        
        # Разделяем имя и фамилию
        name_parts = name.split()
        first_name = name_parts[0] if name_parts else name
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
        
        contact_data = {
            'display_name': name,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'category': 'personal'
        }
        
        result = await self.db.create_contact(user_id, contact_data)
        
        if result:
            phone_str = f"\n📱 {phone}" if phone else ""
            await update.message.reply_text(
                f"✅ **Контакт добавлен!**\n\n"
                f"👤 {name}{phone_str}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Ошибка при добавлении контакта")
    
    async def _search_contacts(self, update: Update, user_id: str, args: list):
        """Поиск контактов"""
        if not args:
            await update.message.reply_text(
                "🔍 Укажи что искать:\n"
                "`/contact search Иван`\n"
                "`/contact search 8999`",
                parse_mode='Markdown'
            )
            return
        
        query = ' '.join(args)
        contacts = await self.db.search_contacts(user_id, query)
        
        if not contacts:
            await update.message.reply_text(
                f"📭 Контакты не найдены: _{query}_",
                parse_mode='Markdown'
            )
            return
        
        lines = [f"🔍 **Найдено ({len(contacts)}):**\n"]
        
        for c in contacts[:10]:
            star = "⭐ " if c.get('is_favorite') else ""
            phone = f"\n   📱 {c['phone']}" if c.get('phone') else ""
            email = f"\n   📧 {c['email']}" if c.get('email') else ""
            company = f"\n   🏢 {c['company']}" if c.get('company') else ""
            
            lines.append(f"{star}**{c['display_name']}**{phone}{email}{company}")
            lines.append("")
        
        await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
    
    async def _delete_contact(self, update: Update, user_id: str, args: list):
        """Удалить контакт"""
        if not args:
            await update.message.reply_text("❌ Укажи имя контакта для удаления")
            return
        
        query = ' '.join(args)
        
        # Сначала найдем контакт
        contacts = await self.db.search_contacts(user_id, query)
        
        if not contacts:
            await update.message.reply_text(f"❌ Контакт не найден: {query}")
            return
        
        if len(contacts) > 1:
            lines = ["⚠️ Найдено несколько контактов:\n"]
            for c in contacts[:5]:
                lines.append(f"• {c['display_name']}")
            lines.append("\nУточни имя для удаления")
            await update.message.reply_text('\n'.join(lines))
            return
        
        # Удаляем
        contact = contacts[0]
        success = await self.db.delete_contact(user_id, contact['id'])
        
        if success:
            await update.message.reply_text(f"🗑️ Контакт удалён: **{contact['display_name']}**", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Ошибка при удалении")
    
    async def _toggle_favorite(self, update: Update, user_id: str, args: list):
        """Добавить/убрать из избранного"""
        if not args:
            await update.message.reply_text("❌ Укажи имя контакта")
            return
        
        query = ' '.join(args)
        contacts = await self.db.search_contacts(user_id, query)
        
        if not contacts:
            await update.message.reply_text(f"❌ Контакт не найден: {query}")
            return
        
        contact = contacts[0]
        result = await self.db.toggle_favorite_contact(user_id, contact['id'])
        
        if result:
            is_fav = result.get('is_favorite', False)
            emoji = "⭐" if is_fav else "✅"
            status = "добавлен в избранное" if is_fav else "убран из избранного"
            await update.message.reply_text(f"{emoji} **{contact['display_name']}** {status}", parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Ошибка")
    
    async def _contact_info(self, update: Update, user_id: str, args: list):
        """Подробная информация о контакте"""
        if not args:
            await update.message.reply_text("❌ Укажи имя контакта")
            return
        
        query = ' '.join(args)
        contacts = await self.db.search_contacts(user_id, query)
        
        if not contacts:
            await update.message.reply_text(f"❌ Контакт не найден: {query}")
            return
        
        c = contacts[0]
        contact = Contact.from_dict(c)
        
        await update.message.reply_text(contact.format_full(), parse_mode='Markdown')
    
    # ==========================================
    # Методы для естественного языка (UnifiedHandler)
    # ==========================================
    
    async def add_contact_natural(self, user_id: str, text: str) -> str:
        """Добавить контакт из естественного языка"""
        # Убираем ключевые слова
        clean_text = re.sub(
            r'(добав|создай|запиши|сохрани|новый)\s*(контакт|номер|телефон)?\s*:?\s*',
            '', text, flags=re.IGNORECASE
        ).strip()
        
        if not clean_text:
            return "❌ Укажи имя и телефон контакта"
        
        # Парсим
        phone = None
        name = clean_text
        
        phone_match = re.search(r'[\+]?[78]?[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}', clean_text)
        if phone_match:
            phone = Helpers.clean_phone(phone_match.group())
            name = clean_text.replace(phone_match.group(), '').strip()
        
        if not name:
            name = "Без имени"
        
        name_parts = name.split()
        first_name = name_parts[0] if name_parts else name
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
        
        contact_data = {
            'display_name': name,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone,
            'category': 'personal'
        }
        
        result = await self.db.create_contact(user_id, contact_data)
        
        if result:
            phone_str = f"\n📱 {phone}" if phone else ""
            return f"✅ **Контакт сохранён!**\n\n👤 {name}{phone_str}"
        else:
            return "❌ Ошибка при сохранении контакта"
    
    async def search_contact_natural(self, user_id: str, text: str) -> str:
        """Поиск контакта из естественного языка"""
        # Убираем ключевые слова
        query = re.sub(
            r'(найди|покажи|поиск|ищи|где)\s*(контакт|номер|телефон)?\s*:?\s*',
            '', text, flags=re.IGNORECASE
        ).strip()
        
        if not query:
            # Показываем все контакты
            contacts = await self.db.get_contacts(user_id, limit=20)
            if not contacts:
                return "📭 У тебя пока нет контактов"
            
            lines = ["📇 **Твои контакты:**\n"]
            for c in contacts[:15]:
                star = "⭐ " if c.get('is_favorite') else ""
                phone = f" 📱 {c['phone']}" if c.get('phone') else ""
                lines.append(f"{star}{c['display_name']}{phone}")
            return '\n'.join(lines)
        
        contacts = await self.db.search_contacts(user_id, query)
        
        if not contacts:
            return f"📭 Контакт не найден: _{query}_"
        
        lines = [f"🔍 **Найдено ({len(contacts)}):**\n"]
        for c in contacts[:5]:
            star = "⭐ " if c.get('is_favorite') else ""
            lines.append(f"{star}**{c['display_name']}**")
            if c.get('phone'):
                lines.append(f"   📱 {c['phone']}")
            if c.get('email'):
                lines.append(f"   📧 {c['email']}")
            lines.append("")
        
        return '\n'.join(lines)
