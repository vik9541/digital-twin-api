"""
Вспомогательные функции
"""

from datetime import datetime, timedelta
from typing import Optional, List, Any
import hashlib
from utils.timezone import now_naive as moscow_now


class Helpers:
    """Вспомогательные функции"""
    
    @staticmethod
    def generate_file_hash(file_data: bytes) -> str:
        """Генерация хеша файла"""
        return hashlib.sha256(file_data).hexdigest()
    
    @staticmethod
    def format_bytes(size_bytes: int) -> str:
        """Форматирование размера файла"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} ТБ"
    
    @staticmethod
    def relative_time(dt: datetime) -> str:
        """Относительное время (5 минут назад, вчера, и т.д.)"""
        now = moscow_now()
        diff = now - dt
        
        if diff < timedelta(minutes=1):
            return "только что"
        elif diff < timedelta(hours=1):
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} мин. назад"
        elif diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} ч. назад"
        elif diff < timedelta(days=2):
            return "вчера"
        elif diff < timedelta(days=7):
            days = diff.days
            return f"{days} дн. назад"
        else:
            return dt.strftime("%d.%m.%Y")
    
    @staticmethod
    def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """Разбить список на части"""
        return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
    
    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Извлечь все числа из текста"""
        import re
        pattern = r'[-+]?\d*[.,]?\d+'
        matches = re.findall(pattern, text)
        
        numbers = []
        for match in matches:
            try:
                numbers.append(float(match.replace(',', '.')))
            except ValueError:
                continue
        
        return numbers
    
    @staticmethod
    def clean_phone(phone: str) -> str:
        """Очистить номер телефона"""
        import re
        # Оставить только цифры
        digits = re.sub(r'\D', '', phone)
        
        # Нормализовать российский номер
        if len(digits) == 11 and digits.startswith('8'):
            digits = '7' + digits[1:]
        elif len(digits) == 10:
            digits = '7' + digits
        
        return '+' + digits if digits else ''
    
    @staticmethod
    def pluralize(count: int, forms: tuple) -> str:
        """
        Склонение слов
        forms = ('задача', 'задачи', 'задач')
        """
        if count % 10 == 1 and count % 100 != 11:
            return forms[0]
        elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
            return forms[1]
        else:
            return forms[2]
    
    @staticmethod
    def mask_string(s: str, visible_start: int = 4, visible_end: int = 4) -> str:
        """Маскирование строки (для токенов, паролей)"""
        if len(s) <= visible_start + visible_end:
            return '*' * len(s)
        
        return s[:visible_start] + '*' * (len(s) - visible_start - visible_end) + s[-visible_end:]
