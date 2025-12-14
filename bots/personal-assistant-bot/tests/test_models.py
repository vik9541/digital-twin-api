"""
Тесты для моделей данных
"""

import pytest
from datetime import datetime, date
from models.project import Project
from models.task import Task
from models.receipt import Receipt, ReceiptItem
from models.health_entry import HealthEntry
from models.user_preferences import UserPreferences


class TestProject:
    """Тесты модели проекта"""
    
    def test_from_dict(self):
        """Тест создания из словаря"""
        data = {
            'id': 'proj-1',
            'user_id': 'user-1',
            'project_name': 'Тестовый проект',
            'status': 'active'
        }
        
        project = Project.from_dict(data)
        
        assert project.id == 'proj-1'
        assert project.project_name == 'Тестовый проект'
        assert project.is_active is True
    
    def test_to_dict(self):
        """Тест преобразования в словарь"""
        project = Project(
            id='proj-1',
            user_id='user-1',
            project_name='Test'
        )
        
        data = project.to_dict()
        
        assert data['id'] == 'proj-1'
        assert data['project_name'] == 'Test'
    
    def test_is_overdue(self):
        """Тест проверки просрочки"""
        from datetime import timedelta
        
        # Просроченный проект
        overdue = Project(
            id='1', user_id='1', project_name='Test',
            deadline=datetime.now() - timedelta(days=1),
            status='active'
        )
        assert overdue.is_overdue is True
        
        # Непросроченный
        not_overdue = Project(
            id='2', user_id='1', project_name='Test',
            deadline=datetime.now() + timedelta(days=1),
            status='active'
        )
        assert not_overdue.is_overdue is False


class TestTask:
    """Тесты модели задачи"""
    
    def test_priority_emoji(self):
        """Тест эмодзи приоритета"""
        high = Task(id='1', user_id='1', task_description='Test', priority='high')
        medium = Task(id='2', user_id='1', task_description='Test', priority='medium')
        low = Task(id='3', user_id='1', task_description='Test', priority='low')
        
        assert high.priority_emoji == '🔴'
        assert medium.priority_emoji == '🟡'
        assert low.priority_emoji == '🟢'
    
    def test_status_checks(self):
        """Тест проверок статуса"""
        pending = Task(id='1', user_id='1', task_description='Test', status='pending')
        done = Task(id='2', user_id='1', task_description='Test', status='done')
        
        assert pending.is_pending is True
        assert pending.is_done is False
        assert done.is_done is True


class TestReceipt:
    """Тесты модели чека"""
    
    def test_from_dict_with_items(self):
        """Тест создания с товарами"""
        data = {
            'id': 'rec-1',
            'user_id': 'user-1',
            'store_name': 'Пятёрочка',
            'total_sum': 500.0,
            'items': [
                {'id': 'item-1', 'receipt_id': 'rec-1', 'item_name': 'Молоко', 'price': 89.0}
            ]
        }
        
        receipt = Receipt.from_dict(data)
        
        assert receipt.store_name == 'Пятёрочка'
        assert receipt.total_sum == 500.0
        assert receipt.items_count == 1
    
    def test_categories(self):
        """Тест получения категорий"""
        receipt = Receipt(id='1', user_id='1')
        receipt.items = [
            ReceiptItem(id='1', receipt_id='1', item_name='Молоко', category='Продукты'),
            ReceiptItem(id='2', receipt_id='1', item_name='Сок', category='Напитки'),
            ReceiptItem(id='3', receipt_id='1', item_name='Хлеб', category='Продукты'),
        ]
        
        categories = receipt.categories
        assert 'Продукты' in categories
        assert 'Напитки' in categories
        assert len(categories) == 2


class TestHealthEntry:
    """Тесты модели записи здоровья"""
    
    def test_type_info(self):
        """Тест информации о типе"""
        food = HealthEntry(id='1', user_id='1', entry_type='food')
        activity = HealthEntry(id='2', user_id='1', entry_type='activity')
        
        assert food.type_name == 'Питание'
        assert food.type_emoji == '🍽️'
        assert activity.type_name == 'Активность'
        assert activity.type_emoji == '🏃'


class TestUserPreferences:
    """Тесты модели настроек пользователя"""
    
    def test_mode_info(self):
        """Тест информации о режиме"""
        prefs = UserPreferences(user_id='1', mode='executor')
        
        assert prefs.mode_name == 'Исполнитель'
        assert 'советов' in prefs.mode_description.lower() or 'выполняю' in prefs.mode_description.lower()
    
    def test_default_values(self):
        """Тест значений по умолчанию"""
        prefs = UserPreferences(user_id='1')
        
        assert prefs.mode == 'executor'
        assert prefs.give_advice is False
        assert prefs.language == 'ru'
        assert prefs.timezone == 'Europe/Moscow'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
