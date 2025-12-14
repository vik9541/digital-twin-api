"""Handlers - Обработчики команд и сообщений"""

import sys
import os

# Добавляем родительскую директорию в путь
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from handlers.commands import CommandsHandler
from handlers.projects_handler import ProjectsHandler
from handlers.tasks_handler import TasksHandler
from handlers.receipts_handler import ReceiptsHandler
from handlers.health_handler import HealthHandler
from handlers.settings_handler import SettingsHandler
from handlers.reminders_handler import RemindersHandler
from handlers.export_handler import ExportHandler
from handlers.microsoft_handler import MicrosoftHandler

__all__ = [
    "CommandsHandler",
    "ProjectsHandler", 
    "TasksHandler",
    "ReceiptsHandler",
    "HealthHandler",
    "SettingsHandler",
    "RemindersHandler",
    "ExportHandler",
    "MicrosoftHandler",
]
