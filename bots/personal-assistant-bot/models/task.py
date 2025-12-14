"""
Модель задачи
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optionalfrom utils.timezone import now_naive as moscow_now

@dataclass
class Task:
    """Модель задачи пользователя"""
    
    id: str
    user_id: str
    task_description: str
    status: str = 'pending'  # pending, in_progress, done
    priority: str = 'medium'  # low, medium, high
    project_id: Optional[str] = None
    created_at: datetime = field(default_factory=moscow_now)
    due_date: Optional[datetime] = None
    
    # Связанные данные
    project_name: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Создать из словаря"""
        return cls(
            id=data.get('id', ''),
            user_id=data.get('user_id', ''),
            task_description=data.get('task_description', ''),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'medium'),
            project_id=data.get('project_id'),
            created_at=data.get('created_at', moscow_now()),
            due_date=data.get('due_date'),
            project_name=data.get('project_name')
        )
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_description': self.task_description,
            'status': self.status,
            'priority': self.priority,
            'project_id': self.project_id,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'due_date': self.due_date.isoformat() if isinstance(self.due_date, datetime) else self.due_date
        }
    
    @property
    def is_pending(self) -> bool:
        return self.status == 'pending'
    
    @property
    def is_done(self) -> bool:
        return self.status == 'done'
    
    @property
    def is_high_priority(self) -> bool:
        return self.priority == 'high'
    
    @property
    def priority_emoji(self) -> str:
        return {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(self.priority, '⚪')
