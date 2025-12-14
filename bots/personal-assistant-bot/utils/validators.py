"""
Валидация данных
"""

import re
from typing import Optional, Tuple


class Validators:
    """Валидация входных данных"""
    
    @staticmethod
    def validate_project_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Валидация названия проекта
        
        Returns:
            (is_valid, error_message)
        """
        if not name:
            return False, "Название проекта не может быть пустым"
        
        if len(name) < 2:
            return False, "Название проекта слишком короткое (мин. 2 символа)"
        
        if len(name) > 100:
            return False, "Название проекта слишком длинное (макс. 100 символов)"
        
        return True, None
    
    @staticmethod
    def validate_task_description(description: str) -> Tuple[bool, Optional[str]]:
        """Валидация описания задачи"""
        if not description:
            return False, "Описание задачи не может быть пустым"
        
        if len(description) < 2:
            return False, "Описание слишком короткое"
        
        if len(description) > 500:
            return False, "Описание слишком длинное (макс. 500 символов)"
        
        return True, None
    
    @staticmethod
    def validate_priority(priority: str) -> Tuple[bool, Optional[str]]:
        """Валидация приоритета"""
        valid_priorities = ['low', 'medium', 'high']
        
        if priority.lower() not in valid_priorities:
            return False, f"Приоритет должен быть: {', '.join(valid_priorities)}"
        
        return True, None
    
    @staticmethod
    def validate_mode(mode: str) -> Tuple[bool, Optional[str]]:
        """Валидация режима работы"""
        valid_modes = ['executor', 'advisor', 'silent', 'detailed']
        
        if mode.lower() not in valid_modes:
            return False, f"Режим должен быть: {', '.join(valid_modes)}"
        
        return True, None
    
    @staticmethod
    def validate_file_size(size_bytes: int, max_mb: int = 20) -> Tuple[bool, Optional[str]]:
        """Валидация размера файла"""
        max_bytes = max_mb * 1024 * 1024
        
        if size_bytes > max_bytes:
            return False, f"Файл слишком большой (макс. {max_mb} МБ)"
        
        return True, None
    
    @staticmethod
    def validate_date(date_str: str) -> Tuple[bool, Optional[str]]:
        """Валидация даты"""
        patterns = [
            r'^\d{2}\.\d{2}\.\d{4}$',  # 13.12.2025
            r'^\d{4}-\d{2}-\d{2}$',     # 2025-12-13
            r'^\d{2}/\d{2}/\d{4}$'      # 13/12/2025
        ]
        
        for pattern in patterns:
            if re.match(pattern, date_str):
                return True, None
        
        return False, "Неверный формат даты. Используйте: ДД.ММ.ГГГГ"
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Очистка пользовательского ввода"""
        if not text:
            return ""
        
        # Удалить лишние пробелы
        text = ' '.join(text.split())
        
        # Ограничить длину
        text = text[:1000]
        
        return text.strip()
