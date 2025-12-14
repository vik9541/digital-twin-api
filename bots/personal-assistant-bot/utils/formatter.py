"""
Форматирование сообщений для Telegram
"""

from typing import List, Dict, Optional
from datetime import datetime


class MessageFormatter:
    """Форматирование сообщений для Telegram"""
    
    @staticmethod
    def format_project_list(projects: List[Dict]) -> str:
        """Форматирование списка проектов"""
        if not projects:
            return "📂 У тебя пока нет проектов."
        
        message = "📂 **ТВОИ ПРОЕКТЫ:**\n\n"
        
        for i, project in enumerate(projects, 1):
            status_emoji = {
                'active': '🟢',
                'done': '✅',
                'archived': '📦'
            }.get(project.get('status', ''), '⚪')
            
            message += f"{i}. {status_emoji} **{project.get('project_name', '')}**\n"
        
        return message
    
    @staticmethod
    def format_task_list(tasks: List[Dict]) -> str:
        """Форматирование списка задач"""
        if not tasks:
            return "✅ У тебя нет активных задач!"
        
        message = "📋 **АКТИВНЫЕ ЗАДАЧИ:**\n\n"
        
        for i, task in enumerate(tasks, 1):
            priority_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(task.get('priority', ''), '⚪')
            
            message += f"{i}. {priority_emoji} {task.get('task_description', '')}\n"
        
        return message
    
    @staticmethod
    def format_receipt(parsed: Dict) -> str:
        """Форматирование результата анализа чека"""
        message = "✅ **ЧЕК ПРОАНАЛИЗИРОВАН**\n\n"
        
        store = parsed.get('store_name', 'Неизвестный магазин')
        message += f"🏪 **{store}**\n"
        
        if parsed.get('receipt_date'):
            message += f"📅 {parsed['receipt_date']}\n"
        
        items = parsed.get('items', [])
        if items:
            message += "\n🛒 **ТОВАРЫ:**\n"
            for item in items:
                message += f"• {item.get('name', '')} - {item.get('price', 0):.0f}₽\n"
        
        total = parsed.get('total_sum', 0)
        message += f"\n💰 **ИТОГО: {total:.0f}₽**"
        
        return message
    
    @staticmethod
    def format_health_report(entries: List[Dict]) -> str:
        """Форматирование отчета о здоровье"""
        if not entries:
            return "📊 Записей за сегодня нет."
        
        message = "📊 **ОТЧЕТ О ЗДОРОВЬЕ**\n\n"
        
        # Группировка по типам
        by_type = {}
        for entry in entries:
            entry_type = entry.get('entry_type', 'note')
            if entry_type not in by_type:
                by_type[entry_type] = []
            by_type[entry_type].append(entry)
        
        type_info = {
            'food': ('🍽️', 'ПИТАНИЕ'),
            'activity': ('🏃', 'АКТИВНОСТЬ'),
            'sleep': ('😴', 'СОН'),
            'habit': ('🧘', 'ПРИВЫЧКИ'),
            'mood': ('😊', 'НАСТРОЕНИЕ')
        }
        
        for entry_type, items in by_type.items():
            emoji, name = type_info.get(entry_type, ('📝', entry_type.upper()))
            message += f"{emoji} **{name}:**\n"
            for item in items:
                message += f"• {item.get('description', '')}\n"
            message += "\n"
        
        return message
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Экранирование специальных символов Markdown"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        
        return text
    
    @staticmethod
    def truncate(text: str, max_length: int = 100, suffix: str = '...') -> str:
        """Обрезать текст до максимальной длины"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
