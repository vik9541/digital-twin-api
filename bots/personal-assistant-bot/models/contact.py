"""
Модель контакта
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional
from utils.timezone import now_naive as moscow_now


@dataclass
class Contact:
    """Модель контакта"""
    
    id: str
    user_id: str
    display_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    phone: Optional[str] = None
    phone_work: Optional[str] = None
    email: Optional[str] = None
    email_work: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    birthday: Optional[date] = None
    notes: Optional[str] = None
    category: str = 'personal'  # personal, work, family, friend, other
    is_favorite: bool = False
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=moscow_now)
    updated_at: datetime = field(default_factory=moscow_now)
    
    CATEGORIES = {
        'personal': {'name': 'Личный', 'emoji': '👤'},
        'work': {'name': 'Рабочий', 'emoji': '💼'},
        'family': {'name': 'Семья', 'emoji': '👨‍👩‍👧'},
        'friend': {'name': 'Друг', 'emoji': '🤝'},
        'other': {'name': 'Другое', 'emoji': '📇'}
    }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Contact':
        return cls(
            id=data.get('id', ''),
            user_id=data.get('user_id', ''),
            display_name=data.get('display_name', ''),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            nickname=data.get('nickname'),
            phone=data.get('phone'),
            phone_work=data.get('phone_work'),
            email=data.get('email'),
            email_work=data.get('email_work'),
            company=data.get('company'),
            job_title=data.get('job_title'),
            birthday=data.get('birthday'),
            notes=data.get('notes'),
            category=data.get('category', 'personal'),
            is_favorite=data.get('is_favorite', False),
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at', moscow_now()),
            updated_at=data.get('updated_at', moscow_now())
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'display_name': self.display_name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'nickname': self.nickname,
            'phone': self.phone,
            'phone_work': self.phone_work,
            'email': self.email,
            'email_work': self.email_work,
            'company': self.company,
            'job_title': self.job_title,
            'birthday': self.birthday.isoformat() if isinstance(self.birthday, date) else self.birthday,
            'notes': self.notes,
            'category': self.category,
            'is_favorite': self.is_favorite,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at
        }
    
    @property
    def category_name(self) -> str:
        return self.CATEGORIES.get(self.category, {}).get('name', 'Контакт')
    
    @property
    def category_emoji(self) -> str:
        return self.CATEGORIES.get(self.category, {}).get('emoji', '📇')
    
    def format_short(self) -> str:
        """Короткий формат для списка"""
        star = "⭐ " if self.is_favorite else ""
        phone_str = f" 📱 {self.phone}" if self.phone else ""
        return f"{star}{self.display_name}{phone_str}"
    
    def format_full(self) -> str:
        """Полный формат"""
        lines = [f"{self.category_emoji} **{self.display_name}**"]
        
        if self.is_favorite:
            lines[0] = f"⭐ {lines[0]}"
        
        if self.phone:
            lines.append(f"📱 {self.phone}")
        if self.phone_work:
            lines.append(f"☎️ {self.phone_work} (раб)")
        if self.email:
            lines.append(f"📧 {self.email}")
        if self.company:
            job = f", {self.job_title}" if self.job_title else ""
            lines.append(f"🏢 {self.company}{job}")
        if self.birthday:
            lines.append(f"🎂 {self.birthday}")
        if self.notes:
            lines.append(f"📝 {self.notes}")
        
        return "\n".join(lines)
