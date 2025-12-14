"""
Тесты для валидаторов
"""

import pytest
from utils.validators import Validators


class TestValidators:
    """Тесты валидации"""
    
    def test_validate_project_name_valid(self):
        """Тест валидного названия проекта"""
        is_valid, error = Validators.validate_project_name("Мой проект")
        assert is_valid is True
        assert error is None
    
    def test_validate_project_name_empty(self):
        """Тест пустого названия"""
        is_valid, error = Validators.validate_project_name("")
        assert is_valid is False
        assert "пустым" in error
    
    def test_validate_project_name_too_short(self):
        """Тест слишком короткого названия"""
        is_valid, error = Validators.validate_project_name("A")
        assert is_valid is False
        assert "короткое" in error
    
    def test_validate_project_name_too_long(self):
        """Тест слишком длинного названия"""
        is_valid, error = Validators.validate_project_name("A" * 101)
        assert is_valid is False
        assert "длинное" in error
    
    def test_validate_task_description_valid(self):
        """Тест валидного описания задачи"""
        is_valid, error = Validators.validate_task_description("Сделать что-то важное")
        assert is_valid is True
        assert error is None
    
    def test_validate_task_description_empty(self):
        """Тест пустого описания"""
        is_valid, error = Validators.validate_task_description("")
        assert is_valid is False
    
    def test_validate_priority_valid(self):
        """Тест валидных приоритетов"""
        for priority in ['low', 'medium', 'high']:
            is_valid, error = Validators.validate_priority(priority)
            assert is_valid is True
            assert error is None
    
    def test_validate_priority_invalid(self):
        """Тест невалидного приоритета"""
        is_valid, error = Validators.validate_priority("critical")
        assert is_valid is False
        assert "должен быть" in error
    
    def test_validate_mode_valid(self):
        """Тест валидных режимов"""
        for mode in ['executor', 'advisor', 'silent', 'detailed']:
            is_valid, error = Validators.validate_mode(mode)
            assert is_valid is True
    
    def test_validate_mode_invalid(self):
        """Тест невалидного режима"""
        is_valid, error = Validators.validate_mode("unknown")
        assert is_valid is False
    
    def test_validate_file_size_valid(self):
        """Тест допустимого размера файла"""
        is_valid, error = Validators.validate_file_size(5 * 1024 * 1024)  # 5 MB
        assert is_valid is True
    
    def test_validate_file_size_too_large(self):
        """Тест слишком большого файла"""
        is_valid, error = Validators.validate_file_size(25 * 1024 * 1024)  # 25 MB
        assert is_valid is False
        assert "большой" in error
    
    def test_validate_date_formats(self):
        """Тест форматов даты"""
        valid_dates = ['13.12.2025', '2025-12-13', '13/12/2025']
        
        for date_str in valid_dates:
            is_valid, error = Validators.validate_date(date_str)
            assert is_valid is True, f"Date {date_str} should be valid"
    
    def test_validate_date_invalid(self):
        """Тест невалидной даты"""
        is_valid, error = Validators.validate_date("invalid")
        assert is_valid is False
    
    def test_sanitize_input(self):
        """Тест очистки ввода"""
        result = Validators.sanitize_input("  Hello   World  ")
        assert result == "Hello World"
    
    def test_sanitize_input_max_length(self):
        """Тест ограничения длины"""
        long_text = "A" * 2000
        result = Validators.sanitize_input(long_text)
        assert len(result) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
