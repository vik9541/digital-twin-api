"""
Тесты для хелперов
"""

import pytest
from datetime import datetime, timedelta
from utils.helpers import Helpers


class TestHelpers:
    """Тесты вспомогательных функций"""
    
    def test_format_bytes(self):
        """Тест форматирования размера файла"""
        assert 'Б' in Helpers.format_bytes(500)
        assert 'КБ' in Helpers.format_bytes(5000)
        assert 'МБ' in Helpers.format_bytes(5000000)
        assert 'ГБ' in Helpers.format_bytes(5000000000)
    
    def test_relative_time_now(self):
        """Тест относительного времени - только что"""
        now = datetime.now()
        result = Helpers.relative_time(now)
        assert 'только что' in result
    
    def test_relative_time_minutes(self):
        """Тест относительного времени - минуты"""
        past = datetime.now() - timedelta(minutes=30)
        result = Helpers.relative_time(past)
        assert 'мин' in result
    
    def test_relative_time_hours(self):
        """Тест относительного времени - часы"""
        past = datetime.now() - timedelta(hours=5)
        result = Helpers.relative_time(past)
        assert 'ч.' in result
    
    def test_relative_time_yesterday(self):
        """Тест относительного времени - вчера"""
        yesterday = datetime.now() - timedelta(days=1, hours=2)
        result = Helpers.relative_time(yesterday)
        assert 'вчера' in result
    
    def test_relative_time_days(self):
        """Тест относительного времени - дни"""
        past = datetime.now() - timedelta(days=3)
        result = Helpers.relative_time(past)
        assert 'дн.' in result
    
    def test_chunk_list(self):
        """Тест разбиения списка"""
        items = [1, 2, 3, 4, 5, 6, 7]
        chunks = Helpers.chunk_list(items, 3)
        
        assert len(chunks) == 3
        assert chunks[0] == [1, 2, 3]
        assert chunks[1] == [4, 5, 6]
        assert chunks[2] == [7]
    
    def test_extract_numbers(self):
        """Тест извлечения чисел"""
        text = "Цена 123.50 руб, количество 5 шт"
        numbers = Helpers.extract_numbers(text)
        
        assert 123.50 in numbers
        assert 5 in numbers
    
    def test_extract_numbers_comma(self):
        """Тест извлечения чисел с запятой"""
        text = "Итого: 1500,75"
        numbers = Helpers.extract_numbers(text)
        
        assert 1500.75 in numbers
    
    def test_clean_phone_russian(self):
        """Тест очистки российского номера"""
        phones = [
            ('+7 (999) 123-45-67', '+79991234567'),
            ('8-999-123-45-67', '+79991234567'),
            ('89991234567', '+79991234567'),
        ]
        
        for input_phone, expected in phones:
            result = Helpers.clean_phone(input_phone)
            assert result == expected, f"Failed for {input_phone}"
    
    def test_pluralize(self):
        """Тест склонения"""
        forms = ('задача', 'задачи', 'задач')
        
        assert Helpers.pluralize(1, forms) == 'задача'
        assert Helpers.pluralize(2, forms) == 'задачи'
        assert Helpers.pluralize(5, forms) == 'задач'
        assert Helpers.pluralize(11, forms) == 'задач'
        assert Helpers.pluralize(21, forms) == 'задача'
        assert Helpers.pluralize(22, forms) == 'задачи'
    
    def test_mask_string(self):
        """Тест маскирования строки"""
        token = "1234567890abcdef"
        result = Helpers.mask_string(token)
        
        assert result.startswith('1234')
        assert result.endswith('cdef')
        assert '*' in result
    
    def test_mask_string_short(self):
        """Тест маскирования короткой строки"""
        short = "abc"
        result = Helpers.mask_string(short)
        assert result == "***"
    
    def test_generate_file_hash(self):
        """Тест генерации хеша"""
        data = b"Hello World"
        hash1 = Helpers.generate_file_hash(data)
        hash2 = Helpers.generate_file_hash(data)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256
    
    def test_generate_file_hash_different(self):
        """Тест разных хешей для разных данных"""
        hash1 = Helpers.generate_file_hash(b"Data 1")
        hash2 = Helpers.generate_file_hash(b"Data 2")
        
        assert hash1 != hash2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
