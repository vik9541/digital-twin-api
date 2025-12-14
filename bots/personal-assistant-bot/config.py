"""
Конфигурация Personal Assistant Bot
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Конфигурация бота"""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Google Cloud Vision (OCR)
    GOOGLE_CLOUD_CREDENTIALS: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # Yandex Market API
    YANDEX_MARKET_API_KEY: str = os.getenv("YANDEX_MARKET_API_KEY", "")
    
    # Microsoft Graph API
    MS_ACCESS_TOKEN: str = os.getenv("MS_ACCESS_TOKEN", "")
    
    # Storage Buckets (Supabase)
    STORAGE_BUCKET_PROJECTS: str = "project-files"
    STORAGE_BUCKET_RECEIPTS: str = "receipts"
    
    # Режим работы
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Лимиты
    MAX_FILE_SIZE_MB: int = 50  # Supabase default
    MAX_PROJECTS_PER_USER: int = 100
    MAX_TASKS_PER_USER: int = 1000
    
    def validate(self) -> list[str]:
        """Проверить наличие обязательных настроек"""
        errors = []
        
        if not self.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN не установлен")
        
        if not self.SUPABASE_URL:
            errors.append("SUPABASE_URL не установлен")
            
        if not self.SUPABASE_KEY:
            errors.append("SUPABASE_KEY не установлен")
            
        return errors


# Глобальный экземпляр конфигурации
config = Config()
