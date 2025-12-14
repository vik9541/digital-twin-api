"""
Модель записи в дневнике здоровья
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optionalfrom utils.timezone import now_naive as moscow_now

@dataclass
class HealthEntry:
    """Модель записи в дневнике здоровья"""
    
    id: str
    user_id: str
    entry_type: str  # food, activity, habit, mood, sleep, measurement
    description: Optional[str] = None
    entry_date: date = field(default_factory=date.today)
    entry_time: Optional[time] = None
    data: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=moscow_now)
    
    ENTRY_TYPES = {
        'food': {'name': 'Питание', 'emoji': '🍽️'},
        'activity': {'name': 'Активность', 'emoji': '🏃'},
        'habit': {'name': 'Привычка', 'emoji': '🧘'},
        'mood': {'name': 'Настроение', 'emoji': '😊'},
        'sleep': {'name': 'Сон', 'emoji': '😴'},
        'measurement': {'name': 'Измерение', 'emoji': '📏'},
        'note': {'name': 'Заметка', 'emoji': '📝'}
    }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HealthEntry':
        return cls(
            id=data.get('id', ''),
            user_id=data.get('user_id', ''),
            entry_type=data.get('entry_type', 'note'),
            description=data.get('description'),
            entry_date=data.get('entry_date', date.today()),
            entry_time=data.get('entry_time'),
            data=data.get('data', {}),
            created_at=data.get('created_at', moscow_now())
        )
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'entry_type': self.entry_type,
            'description': self.description,
            'entry_date': self.entry_date.isoformat() if isinstance(self.entry_date, date) else self.entry_date,
            'entry_time': self.entry_time.isoformat() if isinstance(self.entry_time, time) else self.entry_time,
            'data': self.data,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @property
    def type_name(self) -> str:
        return self.ENTRY_TYPES.get(self.entry_type, {}).get('name', 'Запись')
    
    @property
    def type_emoji(self) -> str:
        return self.ENTRY_TYPES.get(self.entry_type, {}).get('emoji', '📝')
