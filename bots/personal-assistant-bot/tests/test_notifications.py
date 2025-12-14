"""
Тесты для сервиса уведомлений
"""

import pytest
from datetime import datetime, timedelta
from services.notifications import NotificationService, Reminder


class TestNotificationService:
    """Тесты сервиса уведомлений"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        async def mock_send(user_id, text):
            pass
        
        self.service = NotificationService(mock_send)
    
    def test_add_reminder(self):
        """Тест добавления напоминания"""
        reminder = self.service.add_reminder(
            user_id="123",
            text="Тестовое напоминание",
            remind_at=datetime.now() + timedelta(hours=1)
        )
        
        assert reminder.id is not None
        assert reminder.user_id == "123"
        assert reminder.text == "Тестовое напоминание"
        assert reminder.is_active is True
    
    def test_get_user_reminders(self):
        """Тест получения напоминаний пользователя"""
        # Добавить несколько напоминаний
        self.service.add_reminder("user1", "Reminder 1", datetime.now() + timedelta(hours=1))
        self.service.add_reminder("user1", "Reminder 2", datetime.now() + timedelta(hours=2))
        self.service.add_reminder("user2", "Reminder 3", datetime.now() + timedelta(hours=1))
        
        user1_reminders = self.service.get_user_reminders("user1")
        user2_reminders = self.service.get_user_reminders("user2")
        
        assert len(user1_reminders) == 2
        assert len(user2_reminders) == 1
    
    def test_remove_reminder(self):
        """Тест удаления напоминания"""
        reminder = self.service.add_reminder(
            user_id="123",
            text="To remove",
            remind_at=datetime.now() + timedelta(hours=1)
        )
        
        # Удаление
        result = self.service.remove_reminder(reminder.id)
        assert result is True
        
        # Повторное удаление
        result = self.service.remove_reminder(reminder.id)
        assert result is False
    
    def test_parse_reminder_time_minutes(self):
        """Тест парсинга времени - минуты"""
        cases = [
            "через 30 минут",
            "через 5 мин",
        ]
        
        for text in cases:
            result = self.service.parse_reminder_time(text)
            assert result is not None, f"Failed for: {text}"
            assert result > datetime.now()
    
    def test_parse_reminder_time_hours(self):
        """Тест парсинга времени - часы"""
        cases = [
            "через 2 часа",
            "через 1 час",
        ]
        
        for text in cases:
            result = self.service.parse_reminder_time(text)
            assert result is not None, f"Failed for: {text}"
            assert result > datetime.now()
    
    def test_parse_reminder_time_specific(self):
        """Тест парсинга конкретного времени"""
        # "в 15:00" - если время прошло, будет завтра
        result = self.service.parse_reminder_time("в 15:00")
        assert result is not None
    
    def test_parse_reminder_time_tomorrow(self):
        """Тест парсинга на завтра"""
        result = self.service.parse_reminder_time("завтра в 10:00")
        assert result is not None
        assert result.date() == (datetime.now() + timedelta(days=1)).date()
    
    def test_parse_reminder_time_invalid(self):
        """Тест невалидного времени"""
        result = self.service.parse_reminder_time("какой-то текст без времени")
        assert result is None


class TestReminder:
    """Тесты класса Reminder"""
    
    def test_reminder_defaults(self):
        """Тест значений по умолчанию"""
        reminder = Reminder(
            id="test",
            user_id="123",
            text="Test",
            remind_at=datetime.now()
        )
        
        assert reminder.repeat is None
        assert reminder.is_active is True
    
    def test_repeat_options(self):
        """Тест опций повторения"""
        assert 'daily' in Reminder.REPEAT_OPTIONS
        assert 'weekly' in Reminder.REPEAT_OPTIONS
        assert 'monthly' in Reminder.REPEAT_OPTIONS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
