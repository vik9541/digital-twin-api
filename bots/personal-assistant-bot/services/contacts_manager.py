"""
Contacts Manager - улучшенное управление контактами
Включает работу с историей взаимодействий и контекстом разговора
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from utils.timezone import now as moscow_now
import logging

logger = logging.getLogger(__name__)


class ContactsManager:
    """Менеджер контактов с поддержкой взаимодействий"""
    
    def __init__(self, supabase_service):
        self.db = supabase_service
    
    # ========== Контакты ==========
    
    async def add_contact(
        self,
        user_id: str,
        name: str,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        company: Optional[str] = None,
        position: Optional[str] = None,
        category: str = "other",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Добавить новый контакт"""
        contact_data = {
            "user_id": user_id,
            "name": name,
            "phone": phone,
            "email": email,
            "company": company,
            "position": position,
            "category": category,
            "notes": notes,
            "is_favorite": False,
            "created_at": moscow_now().isoformat()
        }
        
        result = self.db.create_contact(contact_data)
        logger.info(f"Contact created: {name} for user {user_id}")
        return result
    
    async def search_contacts(
        self,
        user_id: str,
        query: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Поиск контактов по имени, телефону, email"""
        contacts = self.db.search_contacts(user_id, query)
        
        if category:
            contacts = [c for c in contacts if c.get("category") == category]
        
        return contacts
    
    async def get_contact_by_name(self, user_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Найти контакт по точному имени"""
        contacts = self.db.search_contacts(user_id, name)
        
        # Ищем точное совпадение
        for contact in contacts:
            if contact.get("name", "").lower() == name.lower():
                return contact
        
        # Если точного нет, возвращаем первый похожий
        return contacts[0] if contacts else None
    
    async def get_all_contacts(self, user_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить все контакты пользователя"""
        contacts = self.db.get_contacts(user_id)
        
        if category:
            contacts = [c for c in contacts if c.get("category") == category]
        
        return contacts
    
    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить контакт"""
        updates["updated_at"] = moscow_now().isoformat()
        return self.db.update_contact(contact_id, updates)
    
    async def delete_contact(self, contact_id: str) -> bool:
        """Удалить контакт"""
        return self.db.delete_contact(contact_id)
    
    async def toggle_favorite(self, contact_id: str) -> Dict[str, Any]:
        """Переключить статус избранного"""
        return self.db.toggle_favorite_contact(contact_id)
    
    # ========== Взаимодействия ==========
    
    async def add_interaction(
        self,
        user_id: str,
        contact_id: str,
        interaction_type: str,  # meeting, call, message, email, other
        description: Optional[str] = None,
        outcome: Optional[str] = None,
        follow_up_date: Optional[date] = None,
        follow_up_task: Optional[str] = None
    ) -> Dict[str, Any]:
        """Записать взаимодействие с контактом"""
        data = {
            "user_id": user_id,
            "contact_id": contact_id,
            "interaction_type": interaction_type,
            "description": description,
            "interaction_date": moscow_now().isoformat(),
            "outcome": outcome,
            "follow_up_date": follow_up_date.isoformat() if follow_up_date else None,
            "follow_up_task": follow_up_task,
            "created_at": moscow_now().isoformat()
        }
        
        try:
            result = self.db.client.table("contact_interactions").insert(data).execute()
            logger.info(f"Interaction added: {interaction_type} with contact {contact_id}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error adding interaction: {e}")
            return {}
    
    async def get_contact_interactions(
        self,
        user_id: str,
        contact_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Получить историю взаимодействий с контактом"""
        try:
            result = self.db.client.table("contact_interactions") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("contact_id", contact_id) \
                .order("interaction_date", desc=True) \
                .limit(limit) \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting interactions: {e}")
            return []
    
    async def get_pending_followups(self, user_id: str) -> List[Dict[str, Any]]:
        """Получить взаимодействия с предстоящими follow-up"""
        today = date.today().isoformat()
        try:
            result = self.db.client.table("contact_interactions") \
                .select("*, contacts(name)") \
                .eq("user_id", user_id) \
                .gte("follow_up_date", today) \
                .order("follow_up_date") \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting followups: {e}")
            return []
    
    # ========== Контекст разговора ==========
    
    async def get_context(self, user_id: str) -> Dict[str, Any]:
        """Получить контекст разговора пользователя"""
        try:
            result = self.db.client.table("conversation_context") \
                .select("*") \
                .eq("user_id", user_id) \
                .single() \
                .execute()
            return result.data or {}
        except Exception as e:
            # Контекст не найден - это нормально
            return {}
    
    async def set_context(
        self,
        user_id: str,
        last_contact_id: Optional[str] = None,
        last_contact_name: Optional[str] = None,
        last_intent: Optional[str] = None,
        context_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Установить контекст разговора"""
        data = {
            "user_id": user_id,
            "updated_at": moscow_now().isoformat()
        }
        
        if last_contact_id:
            data["last_contact_id"] = last_contact_id
        if last_contact_name:
            data["last_contact_name"] = last_contact_name
        if last_intent:
            data["last_intent"] = last_intent
        if context_data:
            data["context_data"] = context_data
        
        try:
            # Upsert - вставить или обновить
            result = self.db.client.table("conversation_context") \
                .upsert(data, on_conflict="user_id") \
                .execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error setting context: {e}")
            return {}
    
    async def clear_context(self, user_id: str) -> bool:
        """Очистить контекст разговора"""
        try:
            self.db.client.table("conversation_context") \
                .delete() \
                .eq("user_id", user_id) \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error clearing context: {e}")
            return False
    
    # ========== Форматирование ==========
    
    def format_contact(self, contact: Dict[str, Any], detailed: bool = False) -> str:
        """Форматировать контакт для отображения"""
        name = contact.get("name", "Без имени")
        phone = contact.get("phone")
        email = contact.get("email")
        company = contact.get("company")
        position = contact.get("position")
        category = contact.get("category", "other")
        is_favorite = contact.get("is_favorite", False)
        notes = contact.get("notes")
        
        # Иконка категории
        category_icons = {
            "work": "💼",
            "personal": "👤",
            "family": "👨‍👩‍👧‍👦",
            "friend": "🤝",
            "other": "📇"
        }
        icon = category_icons.get(category, "📇")
        fav = "⭐ " if is_favorite else ""
        
        if detailed:
            lines = [f"{fav}{icon} **{name}**"]
            if company or position:
                job = ", ".join(filter(None, [position, company]))
                lines.append(f"🏢 {job}")
            if phone:
                lines.append(f"📱 {phone}")
            if email:
                lines.append(f"📧 {email}")
            if notes:
                lines.append(f"📝 {notes}")
            return "\n".join(lines)
        else:
            parts = [f"{fav}{icon} {name}"]
            if phone:
                parts.append(f"📱 {phone}")
            elif email:
                parts.append(f"📧 {email}")
            return " — ".join(parts)
    
    def format_interaction(self, interaction: Dict[str, Any]) -> str:
        """Форматировать взаимодействие"""
        type_icons = {
            "meeting": "🤝",
            "call": "📞",
            "message": "💬",
            "email": "📧",
            "other": "📌"
        }
        
        itype = interaction.get("interaction_type", "other")
        icon = type_icons.get(itype, "📌")
        
        date_str = interaction.get("interaction_date", "")[:10]
        description = interaction.get("description", "")
        
        result = f"{icon} {date_str}"
        if description:
            result += f": {description}"
        
        return result
