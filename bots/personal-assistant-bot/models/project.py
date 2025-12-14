"""
Модель проекта
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Project:
    """Модель проекта пользователя"""
    
    id: str
    user_id: str
    project_name: str
    description: Optional[str] = None
    status: str = 'active'  # active, done, archived
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)
    
    # Вычисляемые поля
    files_count: int = 0
    tasks_count: int = 0
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """Создать из словаря"""
        return cls(
            id=data.get('id', ''),
            user_id=data.get('user_id', ''),
            project_name=data.get('project_name', ''),
            description=data.get('description'),
            status=data.get('status', 'active'),
            created_at=data.get('created_at', datetime.now()),
            deadline=data.get('deadline'),
            metadata=data.get('metadata', {}),
            files_count=data.get('files_count', 0),
            tasks_count=data.get('tasks_count', 0)
        )
    
    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_name': self.project_name,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'deadline': self.deadline.isoformat() if isinstance(self.deadline, datetime) else self.deadline,
            'metadata': self.metadata
        }
    
    @property
    def is_active(self) -> bool:
        return self.status == 'active'
    
    @property
    def is_overdue(self) -> bool:
        if not self.deadline:
            return False
        return datetime.now() > self.deadline and self.is_active
