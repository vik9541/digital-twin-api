"""
Диспетчер интентов — определяет тип запроса пользователя.
Единое окно: пользователь пишет обычным текстом, бот сам понимает.
"""

import re
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Intent(Enum):
    """Типы интентов пользователя"""
    TASK = "task"           # Задача / todo
    PROJECT = "project"     # Проект
    RECEIPT = "receipt"     # Чек (фото)
    HEALTH = "health"       # Здоровье / образ жизни
    REMINDER = "reminder"   # Напоминание
    REPORT = "report"       # Отчёт / аналитика
    SMALL_TALK = "small_talk"  # Привет, ок, спасибо
    UNKNOWN = "unknown"     # Не распознано


@dataclass
class ParsedIntent:
    """Результат парсинга интента"""
    intent: Intent
    confidence: float  # 0.0 - 1.0
    payload: Dict[str, Any]  # Извлечённые данные
    original_text: str


# ============================================
# СЛОВАРИ КЛЮЧЕВЫХ СЛОВ ДЛЯ КЛАССИФИКАЦИИ
# ============================================

INTENT_KEYWORDS = {
    Intent.TASK: {
        'high': [
            'задач', 'задачу', 'задачи', 'todo', 'туду',
            'сделать', 'сделай', 'нужно сделать', 
            'добавь задачу', 'запиши задачу', 'новая задача',
            'не забыть', 'не забудь',
        ],
        'medium': [
            'нужно', 'надо', 'необходимо', 
            'запиши', 'запомни', 'добавь',
            'купить', 'позвонить', 'написать', 'отправить',
        ],
    },
    
    Intent.PROJECT: {
        'high': [
            'проект', 'создай проект', 'новый проект',
            'открой проект', 'покажи проект',
        ],
        'medium': [
            'файлы проекта', 'загрузи в проект',
        ],
    },
    
    Intent.HEALTH: {
        'high': [
            'съел', 'съела', 'поел', 'поела', 'ем', 'ела',
            'выпил', 'выпила', 'пью',
            'курил', 'курила', 'покурил', 'покурила', 'пошёл курить', 'пошел курить',
            'сигарет', 'курение',
            'тренировка', 'тренировался', 'занимался', 'занималась',
            'пробежал', 'пробежала', 'бегал', 'бегала',
            'спал', 'спала', 'проснулся', 'проснулась', 'лёг спать', 'лег спать',
            'вес', 'взвесился', 'взвесилась',
        ],
        'medium': [
            'здоровье', 'дневник', 'самочувствие',
            'завтрак', 'обед', 'ужин', 'перекус',
            'активность', 'шаги', 'прогулка',
        ],
    },
    
    Intent.REMINDER: {
        'high': [
            'напомни', 'напомнить', 'напоминание',
            'через минут', 'через час', 'через часа', 'через часов',
            r'в котор', r'в \d{1,2}:\d{2}', r'в \d{1,2} час',
        ],
        'medium': [
            'не забудь', 'позже', 'потом напомни',
        ],
    },
    
    Intent.REPORT: {
        'high': [
            'отчёт', 'отчет', 'статистика', 'аналитика',
            'покажи за', 'за неделю', 'за месяц', 'за день',
            'сколько потратил', 'сколько курил', 'сколько съел',
        ],
        'medium': [
            'итоги', 'результаты', 'сводка', 'summary',
        ],
    },
    
    Intent.SMALL_TALK: {
        'high': [
            'привет', 'здравствуй', 'hi', 'hello', 'хай',
            'пока', 'до свидания', 'bye',
            'спасибо', 'благодарю', 'thanks',
            'ок', 'окей', 'okay', 'хорошо', 'понял', 'поняла',
            'как дела', 'что умеешь',
        ],
        'medium': [],
    },
}


# ============================================
# ПАТТЕРНЫ ДЛЯ ИЗВЛЕЧЕНИЯ ДАННЫХ
# ============================================

PATTERNS = {
    # Время для напоминаний
    'reminder_relative': [
        r'через\s+(\d+)\s*(минут|мин|час|часа|часов)',
        r'через\s+(полчаса|час)',
    ],
    'reminder_absolute': [
        r'в\s*(\d{1,2}):(\d{2})',
        r'в\s*(\d{1,2})\s*час',
        r'завтра\s+в\s*(\d{1,2}):?(\d{2})?',
    ],
    
    # Дедлайн для задач
    'deadline': [
        r'до\s+(понедельника|вторника|среды|четверга|пятницы|субботы|воскресенья|пн|вт|ср|чт|пт|сб|вс)',
        r'до\s+(\d{1,2})[./](\d{1,2})',
        r'к\s+(понедельнику|вторнику|среде|четвергу|пятнице|субботе|воскресенью)',
        r'(сегодня|завтра|послезавтра)',
    ],
    
    # Время для здоровья
    'time': [
        r'(\d{1,2}):(\d{2})',
        r'в\s*(\d{1,2})\s*час',
    ],
}


class IntentDispatcher:
    """Диспетчер для определения интента и извлечения данных"""
    
    def dispatch(self, text: str, has_photo: bool = False) -> ParsedIntent:
        """
        Определить интент сообщения.
        
        Args:
            text: Текст сообщения
            has_photo: Есть ли фото в сообщении
            
        Returns:
            ParsedIntent с типом интента и извлечёнными данными
        """
        text_lower = text.lower().strip()
        
        # Приоритет 1: Фото → скорее всего чек
        if has_photo:
            return ParsedIntent(
                intent=Intent.RECEIPT,
                confidence=0.9,
                payload={'has_photo': True, 'caption': text},
                original_text=text
            )
        
        # Приоритет 2: Проверяем по ключевым словам
        scores = self._calculate_scores(text_lower)
        
        # Находим интент с максимальным score
        best_intent = Intent.UNKNOWN
        best_score = 0.0
        
        for intent, score in scores.items():
            if score > best_score:
                best_score = score
                best_intent = intent
        
        # Если score слишком низкий — UNKNOWN
        if best_score < 0.3:
            best_intent = Intent.UNKNOWN
        
        # Извлекаем payload в зависимости от интента
        payload = self._extract_payload(best_intent, text, text_lower)
        
        return ParsedIntent(
            intent=best_intent,
            confidence=best_score,
            payload=payload,
            original_text=text
        )
    
    def _calculate_scores(self, text_lower: str) -> Dict[Intent, float]:
        """Посчитать score для каждого интента"""
        scores = {}
        
        for intent, keywords in INTENT_KEYWORDS.items():
            score = 0.0
            
            # High-priority keywords
            for kw in keywords.get('high', []):
                if re.search(kw, text_lower):
                    score += 0.5
            
            # Medium-priority keywords
            for kw in keywords.get('medium', []):
                if kw in text_lower:
                    score += 0.2
            
            # Нормализуем до 1.0
            scores[intent] = min(score, 1.0)
        
        return scores
    
    def _extract_payload(self, intent: Intent, text: str, text_lower: str) -> Dict[str, Any]:
        """Извлечь данные из текста в зависимости от интента"""
        payload = {}
        
        if intent == Intent.TASK:
            payload = self._extract_task_payload(text, text_lower)
        
        elif intent == Intent.REMINDER:
            payload = self._extract_reminder_payload(text, text_lower)
        
        elif intent == Intent.HEALTH:
            payload = self._extract_health_payload(text, text_lower)
        
        elif intent == Intent.PROJECT:
            payload = self._extract_project_payload(text, text_lower)
        
        elif intent == Intent.REPORT:
            payload = self._extract_report_payload(text, text_lower)
        
        return payload
    
    def _extract_task_payload(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Извлечь данные задачи"""
        payload = {'description': text}
        
        # Убрать вводные слова
        description = text
        for prefix in ['задача:', 'задачу:', 'запиши задачу', 'добавь задачу', 
                       'сделать', 'нужно', 'надо', 'необходимо']:
            if text_lower.startswith(prefix):
                description = text[len(prefix):].strip()
                break
        
        # Поиск дедлайна
        deadline = None
        for pattern in PATTERNS['deadline']:
            match = re.search(pattern, text_lower)
            if match:
                deadline = match.group(0)
                # Убрать дедлайн из описания
                description = re.sub(pattern, '', description, flags=re.IGNORECASE).strip()
                break
        
        payload['description'] = description.strip(' ,:')
        payload['deadline'] = deadline
        
        return payload
    
    def _extract_reminder_payload(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Извлечь данные напоминания"""
        payload = {'text': text, 'time_str': None, 'is_relative': False}
        
        # Относительное время (через X минут)
        for pattern in PATTERNS['reminder_relative']:
            match = re.search(pattern, text_lower)
            if match:
                payload['time_str'] = match.group(0)
                payload['is_relative'] = True
                # Текст напоминания — то что после времени
                reminder_text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
                reminder_text = re.sub(r'^напомни\s*', '', reminder_text, flags=re.IGNORECASE).strip()
                payload['text'] = reminder_text or "Напоминание"
                break
        
        # Абсолютное время (в 15:00)
        if not payload['time_str']:
            for pattern in PATTERNS['reminder_absolute']:
                match = re.search(pattern, text_lower)
                if match:
                    payload['time_str'] = match.group(0)
                    payload['is_relative'] = False
                    reminder_text = re.sub(pattern, '', text, flags=re.IGNORECASE).strip()
                    reminder_text = re.sub(r'^напомни\s*', '', reminder_text, flags=re.IGNORECASE).strip()
                    payload['text'] = reminder_text or "Напоминание"
                    break
        
        return payload
    
    def _extract_health_payload(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Извлечь данные для дневника здоровья"""
        payload = {'description': text, 'entry_type': 'other', 'time': None}
        
        # Определить тип записи
        if any(kw in text_lower for kw in ['съел', 'съела', 'поел', 'ем', 'завтрак', 'обед', 'ужин', 'перекус', 'выпил']):
            payload['entry_type'] = 'food'
        elif any(kw in text_lower for kw in ['курил', 'курила', 'покурил', 'сигарет', 'курение', 'курить']):
            payload['entry_type'] = 'habit'
            payload['habit_type'] = 'smoking'
        elif any(kw in text_lower for kw in ['тренировка', 'бегал', 'пробежал', 'занимался', 'зал', 'спорт']):
            payload['entry_type'] = 'activity'
        elif any(kw in text_lower for kw in ['спал', 'проснулся', 'лёг спать', 'сон']):
            payload['entry_type'] = 'sleep'
        elif any(kw in text_lower for kw in ['вес', 'взвесился', 'давление', 'пульс']):
            payload['entry_type'] = 'measurement'
        
        # Извлечь время
        for pattern in PATTERNS['time']:
            match = re.search(pattern, text_lower)
            if match:
                payload['time'] = match.group(0)
                break
        
        return payload
    
    def _extract_project_payload(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Извлечь данные проекта"""
        payload = {'action': 'info', 'name': None}
        
        if any(kw in text_lower for kw in ['создай проект', 'новый проект']):
            payload['action'] = 'create'
            # Извлечь название
            name = re.sub(r'(создай|новый)\s*проект\s*', '', text, flags=re.IGNORECASE).strip()
            payload['name'] = name if name else None
        
        elif any(kw in text_lower for kw in ['список проект', 'мои проект', 'покажи проект']):
            payload['action'] = 'list'
        
        elif 'открой проект' in text_lower:
            payload['action'] = 'open'
            name = re.sub(r'открой\s*проект\s*', '', text, flags=re.IGNORECASE).strip()
            payload['name'] = name if name else None
        
        return payload
    
    def _extract_report_payload(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Извлечь данные для отчёта"""
        payload = {'report_type': 'general', 'period': 'day'}
        
        # Тип отчёта
        if any(kw in text_lower for kw in ['здоровь', 'курен', 'еда', 'питан']):
            payload['report_type'] = 'health'
        elif any(kw in text_lower for kw in ['расход', 'траты', 'чек', 'покупк']):
            payload['report_type'] = 'expenses'
        elif any(kw in text_lower for kw in ['задач', 'дел']):
            payload['report_type'] = 'tasks'
        elif any(kw in text_lower for kw in ['проект']):
            payload['report_type'] = 'projects'
        
        # Период
        if 'неделю' in text_lower or 'неделя' in text_lower or '7 дней' in text_lower:
            payload['period'] = 'week'
        elif 'месяц' in text_lower or '30 дней' in text_lower:
            payload['period'] = 'month'
        elif 'сегодня' in text_lower or 'день' in text_lower:
            payload['period'] = 'day'
        
        return payload


# Глобальный экземпляр диспетчера
dispatcher = IntentDispatcher()


def dispatch_message(text: str, has_photo: bool = False) -> ParsedIntent:
    """
    Главная функция — определить интент сообщения.
    
    Пример:
        result = dispatch_message("Напомни через 30 минут позвонить")
        print(result.intent)  # Intent.REMINDER
        print(result.payload)  # {'text': 'позвонить', 'time_str': 'через 30 минут', ...}
    """
    return dispatcher.dispatch(text, has_photo)
