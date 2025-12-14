"""
Тесты для утилит форматирования
"""

import pytest
from utils.formatter import MessageFormatter


class TestMessageFormatter:
    """Тесты форматирования сообщений"""
    
    def test_format_project_list_empty(self):
        """Тест пустого списка проектов"""
        result = MessageFormatter.format_project_list([])
        assert "нет проектов" in result.lower()
    
    def test_format_project_list(self):
        """Тест форматирования проектов"""
        projects = [
            {'project_name': 'Проект 1', 'status': 'active'},
            {'project_name': 'Проект 2', 'status': 'done'},
        ]
        result = MessageFormatter.format_project_list(projects)
        
        assert 'Проект 1' in result
        assert 'Проект 2' in result
        assert '🟢' in result  # active
        assert '✅' in result  # done
    
    def test_format_task_list_empty(self):
        """Тест пустого списка задач"""
        result = MessageFormatter.format_task_list([])
        assert "нет" in result.lower() and "задач" in result.lower()
    
    def test_format_task_list(self):
        """Тест форматирования задач"""
        tasks = [
            {'task_description': 'Важная задача', 'priority': 'high'},
            {'task_description': 'Обычная задача', 'priority': 'medium'},
        ]
        result = MessageFormatter.format_task_list(tasks)
        
        assert 'Важная задача' in result
        assert 'Обычная задача' in result
        assert '🔴' in result  # high priority
        assert '🟡' in result  # medium priority
    
    def test_format_receipt(self):
        """Тест форматирования чека"""
        receipt_data = {
            'store_name': 'Пятёрочка',
            'receipt_date': '13.12.2025',
            'items': [
                {'name': 'Молоко', 'price': 89},
                {'name': 'Хлеб', 'price': 45},
            ],
            'total_sum': 134
        }
        result = MessageFormatter.format_receipt(receipt_data)
        
        assert 'Пятёрочка' in result
        assert 'Молоко' in result
        assert '134' in result
    
    def test_format_health_report_empty(self):
        """Тест пустого отчета о здоровье"""
        result = MessageFormatter.format_health_report([])
        assert "нет" in result.lower()
    
    def test_format_health_report(self):
        """Тест форматирования отчета о здоровье"""
        entries = [
            {'entry_type': 'food', 'description': 'Овсянка на завтрак'},
            {'entry_type': 'activity', 'description': 'Пробежка 5 км'},
        ]
        result = MessageFormatter.format_health_report(entries)
        
        assert 'Овсянка' in result
        assert 'Пробежка' in result
        assert '🍽️' in result  # food emoji
        assert '🏃' in result  # activity emoji
    
    def test_escape_markdown(self):
        """Тест экранирования Markdown"""
        text = "Hello *world* [test]"
        result = MessageFormatter.escape_markdown(text)
        
        assert '\\*' in result
        assert '\\[' in result
    
    def test_truncate(self):
        """Тест обрезки текста"""
        long_text = "A" * 200
        result = MessageFormatter.truncate(long_text, max_length=100)
        
        assert len(result) == 100
        assert result.endswith('...')
    
    def test_truncate_short_text(self):
        """Тест обрезки короткого текста"""
        short_text = "Short text"
        result = MessageFormatter.truncate(short_text, max_length=100)
        
        assert result == short_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
