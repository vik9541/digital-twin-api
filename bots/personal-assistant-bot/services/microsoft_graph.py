"""
Сервис интеграции с Microsoft Graph API
Управление контактами, календарем, почтой
"""

import aiohttp
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MicrosoftGraphService:
    """Сервис для работы с Microsoft Graph API"""
    
    BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Выполнение запроса к Graph API"""
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            try:
                if method == "GET":
                    async with session.get(url, headers=self.headers) as resp:
                        return await resp.json()
                elif method == "POST":
                    async with session.post(url, headers=self.headers, json=data) as resp:
                        return await resp.json()
                elif method == "PATCH":
                    async with session.patch(url, headers=self.headers, json=data) as resp:
                        return await resp.json()
                elif method == "DELETE":
                    async with session.delete(url, headers=self.headers) as resp:
                        if resp.status == 204:
                            return {"success": True}
                        return await resp.json()
            except Exception as e:
                logger.error(f"Graph API error: {e}")
                return {"error": str(e)}
    
    # ==================== КОНТАКТЫ ====================
    
    async def get_contacts(self, top: int = 100, skip: int = 0) -> List[Dict]:
        """Получить список контактов"""
        endpoint = f"me/contacts?$top={top}&$skip={skip}&$orderby=displayName"
        result = await self._request("GET", endpoint)
        return result.get("value", [])
    
    async def search_contacts(self, query: str) -> List[Dict]:
        """Поиск контактов"""
        endpoint = f"me/contacts?$filter=contains(displayName,'{query}') or contains(emailAddresses/any(e:e/address),'{query}')"
        result = await self._request("GET", endpoint)
        return result.get("value", [])
    
    async def create_contact(self, contact_data: Dict) -> Dict:
        """Создать контакт"""
        return await self._request("POST", "me/contacts", contact_data)
    
    async def update_contact(self, contact_id: str, contact_data: Dict) -> Dict:
        """Обновить контакт"""
        return await self._request("PATCH", f"me/contacts/{contact_id}", contact_data)
    
    async def delete_contact(self, contact_id: str) -> Dict:
        """Удалить контакт"""
        return await self._request("DELETE", f"me/contacts/{contact_id}")
    
    async def get_contact_by_id(self, contact_id: str) -> Dict:
        """Получить контакт по ID"""
        return await self._request("GET", f"me/contacts/{contact_id}")
    
    # ==================== КАЛЕНДАРЬ ====================
    
    async def get_calendar_events(self, days: int = 7) -> List[Dict]:
        """Получить события календаря на ближайшие дни"""
        start = datetime.utcnow().isoformat() + "Z"
        end = (datetime.utcnow() + timedelta(days=days)).isoformat() + "Z"
        
        endpoint = f"me/calendarView?startDateTime={start}&endDateTime={end}&$orderby=start/dateTime"
        result = await self._request("GET", endpoint)
        return result.get("value", [])
    
    async def create_event(self, event_data: Dict) -> Dict:
        """Создать событие в календаре"""
        return await self._request("POST", "me/events", event_data)
    
    async def create_reminder(self, title: str, when: datetime, description: str = "") -> Dict:
        """Создать напоминание (событие с оповещением)"""
        event_data = {
            "subject": title,
            "body": {
                "contentType": "text",
                "content": description
            },
            "start": {
                "dateTime": when.isoformat(),
                "timeZone": "Europe/Moscow"
            },
            "end": {
                "dateTime": (when + timedelta(minutes=30)).isoformat(),
                "timeZone": "Europe/Moscow"
            },
            "isReminderOn": True,
            "reminderMinutesBeforeStart": 15
        }
        return await self.create_event(event_data)
    
    # ==================== ПОЧТА ====================
    
    async def get_recent_emails(self, top: int = 10) -> List[Dict]:
        """Получить последние письма"""
        endpoint = f"me/messages?$top={top}&$orderby=receivedDateTime desc"
        result = await self._request("GET", endpoint)
        return result.get("value", [])
    
    async def get_unread_count(self) -> int:
        """Количество непрочитанных писем"""
        endpoint = "me/mailFolders/inbox?$select=unreadItemCount"
        result = await self._request("GET", endpoint)
        return result.get("unreadItemCount", 0)
    
    async def send_email(self, to: str, subject: str, body: str) -> Dict:
        """Отправить email"""
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "text",
                    "content": body
                },
                "toRecipients": [
                    {"emailAddress": {"address": to}}
                ]
            }
        }
        return await self._request("POST", "me/sendMail", message)
    
    # ==================== ПРОФИЛЬ ====================
    
    async def get_profile(self) -> Dict:
        """Получить профиль пользователя"""
        return await self._request("GET", "me")
    
    async def validate_token(self) -> bool:
        """Проверить валидность токена"""
        result = await self.get_profile()
        return "error" not in result and "id" in result


# Форматирование контактов
def format_contact_for_graph(
    display_name: str,
    email: str = None,
    phone: str = None,
    company: str = None,
    job_title: str = None,
    notes: str = None
) -> Dict:
    """Форматирование данных контакта для Graph API"""
    
    contact = {
        "displayName": display_name,
        "givenName": display_name.split()[0] if display_name else ""
    }
    
    # Фамилия (если есть)
    name_parts = display_name.split() if display_name else []
    if len(name_parts) > 1:
        contact["surname"] = " ".join(name_parts[1:])
    
    # Email
    if email:
        contact["emailAddresses"] = [
            {"address": email, "name": display_name}
        ]
    
    # Телефон
    if phone:
        contact["mobilePhone"] = phone
    
    # Компания
    if company:
        contact["companyName"] = company
    
    # Должность
    if job_title:
        contact["jobTitle"] = job_title
    
    # Заметки
    if notes:
        contact["personalNotes"] = notes
    
    return contact
