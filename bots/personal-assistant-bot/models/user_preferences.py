"""
Модель настроек пользователя
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserPreferences:
    """Модель настроек пользователя"""
    
    user_id: str
    mode: str = 'executor'  # executor, advisor, silent, detailed
    give_advice: bool = False
    language: str = 'ru'
    timezone: str = 'Europe/Moscow'
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    MODES = {
        'executor': {
            'name': 'Исполнитель',
            'description': 'Только выполняю задачи, без советов'
        },
        'advisor': {
            'name': 'Советник',
            'description': 'Даю рекомендации и советы'
        },
        'silent': {
            'name': 'Тихий',
            'description': 'Минимум текста, только результаты'
        },
        'detailed': {
            'name': 'Подробный',
            'description': 'Детальные объяснения всего'
        }
    }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserPreferences':
        return cls(
            user_id=data.get('user_id', ''),
            mode=data.get('mode', 'executor'),
            give_advice=data.get('give_advice', False),
            language=data.get('language', 'ru'),
            timezone=data.get('timezone', 'Europe/Moscow'),
            metadata=data.get('metadata', {}),
            created_at=data.get('created_at', datetime.now()),
            updated_at=data.get('updated_at', datetime.now())
        )
    
    def to_dict(self) -> dict:
        return {
            'user_id': self.user_id,
            'mode': self.mode,
            'give_advice': self.give_advice,
            'language': self.language,
            'timezone': self.timezone,
            'metadata': self.metadata
        }
    
    @property
    def mode_name(self) -> str:
        return self.MODES.get(self.mode, {}).get('name', 'Исполнитель')
    
    @property
    def mode_description(self) -> str:
        return self.MODES.get(self.mode, {}).get('description', '')
