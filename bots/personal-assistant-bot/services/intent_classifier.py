"""
Intent Classifier - классификатор намерений пользователя
Определяет тип запроса по ключевым словам и паттернам
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Tuple


class Intent(Enum):
    """Типы намерений пользователя"""
    # Рабочее время
    WORK_ARRIVAL = "work_arrival"           # Пришёл на работу
    WORK_DEPARTURE = "work_departure"       # Ушёл с работы
    WORK_BREAK_START = "work_break_start"   # Начал перерыв
    WORK_BREAK_END = "work_break_end"       # Закончил перерыв
    WORK_STATUS = "work_status"             # Статус рабочего дня
    WORK_REPORT = "work_report"             # Отчёт по рабочему времени
    
    # Контакты
    CONTACT_ADD = "contact_add"             # Добавить контакт
    CONTACT_SEARCH = "contact_search"       # Найти контакт
    CONTACT_INFO = "contact_info"           # Информация о контакте
    CONTACT_LIST = "contact_list"           # Список контактов
    CONTACT_DELETE = "contact_delete"       # Удалить контакт
    CONTACT_INTERACTION = "contact_interaction"  # Встреча/звонок с контактом
    
    # Задачи
    TASK_ADD = "task_add"                   # Добавить задачу
    TASK_LIST = "task_list"                 # Список задач
    TASK_COMPLETE = "task_complete"         # Завершить задачу
    TASK_DELETE = "task_delete"             # Удалить задачу
    
    # Здоровье
    HEALTH_LOG = "health_log"               # Записать состояние здоровья
    HEALTH_STATUS = "health_status"         # Статус здоровья
    
    # Чеки/финансы
    RECEIPT_ADD = "receipt_add"             # Добавить чек
    RECEIPT_LIST = "receipt_list"           # Список чеков
    
    # Общение
    GREETING = "greeting"                   # Приветствие
    THANKS = "thanks"                       # Благодарность
    HELP = "help"                           # Помощь
    
    # Неизвестно
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Результат классификации"""
    intent: Intent
    confidence: float  # 0.0 - 1.0
    extracted_data: dict  # Извлечённые данные (имя контакта, время и т.д.)
    raw_text: str


class IntentClassifier:
    """Классификатор намерений по ключевым словам"""
    
    def __init__(self):
        # Паттерны для каждого интента (регулярные выражения)
        self.patterns = {
            # Рабочее время
            Intent.WORK_ARRIVAL: [
                r"приш[её]л на работу",
                r"пришла на работу",
                r"я на работе",
                r"начал работать",
                r"начала работать",
                r"на месте",
                r"приступил к работе",
            ],
            Intent.WORK_DEPARTURE: [
                r"уш[её]л с работы",
                r"ушла с работы",
                r"закончил работ",
                r"закончила работ",
                r"ухожу с работы",
                r"домой иду",
                r"иду домой",
                r"рабочий день окончен",
                r"завершил работу",
            ],
            Intent.WORK_BREAK_START: [
                r"ушёл на обед",
                r"ушла на обед",
                r"перерыв",
                r"на обеде",
                r"обедаю",
            ],
            Intent.WORK_BREAK_END: [
                r"вернулся с обеда",
                r"вернулась с обеда",
                r"обед закончил",
                r"конец перерыва",
            ],
            Intent.WORK_STATUS: [
                r"статус.*работ",
                r"сколько.*работал",
                r"сколько.*отработал",
                r"рабочий статус",
            ],
            Intent.WORK_REPORT: [
                r"отчёт.*работ",
                r"отчет.*работ",
                r"рабочий.*отчёт",
                r"статистика.*работ",
            ],
            
            # Контакты
            Intent.CONTACT_ADD: [
                r"добав(?:ь|ить).*контакт",
                r"запиши.*контакт",
                r"сохрани.*контакт",
                r"новый контакт",
                r"запомни.*(?:телефон|номер|email|почт)",
            ],
            Intent.CONTACT_SEARCH: [
                r"найди.*контакт",
                r"поиск.*контакт",
                r"найти.*(?:телефон|номер|email)",
                r"какой.*(?:телефон|номер|email)",
            ],
            Intent.CONTACT_INFO: [
                r"(?:информация|инфо).*о\s+\w+",
                r"расскажи.*о\s+\w+",
                r"кто.*так(?:ой|ая)\s+\w+",
            ],
            Intent.CONTACT_LIST: [
                r"список.*контакт",
                r"все.*контакт",
                r"мои.*контакт",
                r"покажи.*контакт",
            ],
            Intent.CONTACT_DELETE: [
                r"удали.*контакт",
                r"убери.*контакт",
            ],
            Intent.CONTACT_INTERACTION: [
                r"встреч(?:а|ался|алась).*с\s+\w+",
                r"созвонил(?:ся|ась).*с\s+\w+",
                r"звонил.*\w+",
                r"виделся.*с\s+\w+",
                r"общался.*с\s+\w+",
            ],
            
            # Задачи
            Intent.TASK_ADD: [
                r"добав(?:ь|ить).*задач",
                r"создай.*задач",
                r"напомни.*(?:о|про)",
                r"нужно.*сделать",
                r"не забыть",
            ],
            Intent.TASK_LIST: [
                r"список.*задач",
                r"мои.*задач",
                r"что.*(?:сделать|нужно)",
                r"покажи.*задач",
            ],
            Intent.TASK_COMPLETE: [
                r"выполн(?:ил|ена|ено).*задач",
                r"завершил.*задач",
                r"готов(?:о|а).*задач",
                r"сделал.*задач",
            ],
            Intent.TASK_DELETE: [
                r"удали.*задач",
                r"убери.*задач",
                r"отмени.*задач",
            ],
            
            # Здоровье
            Intent.HEALTH_LOG: [
                r"(?:самочувствие|состояние).*(?:\d|хорош|плох|норм)",
                r"давление\s+\d+",
                r"пульс\s+\d+",
                r"вес\s+\d+",
                r"голова.*болит",
                r"чувствую.*себя",
            ],
            Intent.HEALTH_STATUS: [
                r"(?:как|моё).*здоровь",
                r"статистика.*здоровь",
                r"история.*здоровь",
            ],
            
            # Чеки
            Intent.RECEIPT_ADD: [
                r"чек\s+(?:на\s+)?\d+",
                r"потратил\s+\d+",
                r"купил.*за\s+\d+",
                r"расход\s+\d+",
            ],
            Intent.RECEIPT_LIST: [
                r"(?:мои|все).*чеки",
                r"расходы.*за",
                r"траты.*за",
            ],
            
            # Общение
            Intent.GREETING: [
                r"^привет",
                r"^здравствуй",
                r"^добр(?:ое|ый|ого)",
                r"^хай",
                r"^hi$",
                r"^hello",
            ],
            Intent.THANKS: [
                r"спасибо",
                r"благодар",
                r"молодец",
            ],
            Intent.HELP: [
                r"^помо(?:щь|ги)",
                r"что.*умеешь",
                r"как.*пользоваться",
                r"^/help",
            ],
        }
        
        # Ключевые слова для извлечения данных
        self.extraction_patterns = {
            "contact_name": r"(?:с\s+|контакт\s+|о\s+)([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)",
            "phone": r"(\+?[78][\d\s\-]{9,11})",
            "email": r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)",
            "amount": r"(\d+(?:[.,]\d+)?)\s*(?:руб|₽|р\.?)?",
            "time": r"(\d{1,2}:\d{2})",
            "date": r"(\d{1,2}[./]\d{1,2}(?:[./]\d{2,4})?)",
        }
    
    def classify(self, text: str) -> ClassificationResult:
        """Классифицировать текст пользователя"""
        text_lower = text.lower().strip()
        
        best_intent = Intent.UNKNOWN
        best_confidence = 0.0
        
        for intent, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    # Чем длиннее совпадение, тем выше уверенность
                    confidence = len(match.group()) / len(text_lower)
                    confidence = min(confidence * 2, 1.0)  # Нормализация
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
        
        # Извлечение данных
        extracted_data = self._extract_data(text)
        
        return ClassificationResult(
            intent=best_intent,
            confidence=best_confidence,
            extracted_data=extracted_data,
            raw_text=text
        )
    
    def _extract_data(self, text: str) -> dict:
        """Извлечь данные из текста"""
        data = {}
        
        for key, pattern in self.extraction_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[key] = match.group(1)
        
        return data
    
    def get_intent_description(self, intent: Intent) -> str:
        """Получить описание интента"""
        descriptions = {
            Intent.WORK_ARRIVAL: "Отметка о приходе на работу",
            Intent.WORK_DEPARTURE: "Отметка об уходе с работы",
            Intent.WORK_BREAK_START: "Начало перерыва",
            Intent.WORK_BREAK_END: "Конец перерыва",
            Intent.WORK_STATUS: "Запрос статуса рабочего дня",
            Intent.WORK_REPORT: "Запрос отчёта по рабочему времени",
            
            Intent.CONTACT_ADD: "Добавление нового контакта",
            Intent.CONTACT_SEARCH: "Поиск контакта",
            Intent.CONTACT_INFO: "Информация о контакте",
            Intent.CONTACT_LIST: "Список контактов",
            Intent.CONTACT_DELETE: "Удаление контакта",
            Intent.CONTACT_INTERACTION: "Запись взаимодействия с контактом",
            
            Intent.TASK_ADD: "Добавление задачи",
            Intent.TASK_LIST: "Список задач",
            Intent.TASK_COMPLETE: "Завершение задачи",
            Intent.TASK_DELETE: "Удаление задачи",
            
            Intent.HEALTH_LOG: "Запись состояния здоровья",
            Intent.HEALTH_STATUS: "Статус здоровья",
            
            Intent.RECEIPT_ADD: "Добавление чека",
            Intent.RECEIPT_LIST: "Список чеков",
            
            Intent.GREETING: "Приветствие",
            Intent.THANKS: "Благодарность",
            Intent.HELP: "Запрос помощи",
            
            Intent.UNKNOWN: "Неизвестный запрос",
        }
        return descriptions.get(intent, "Неизвестный интент")


# Синглтон для использования
_classifier_instance: Optional[IntentClassifier] = None


def get_classifier() -> IntentClassifier:
    """Получить экземпляр классификатора"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntentClassifier()
    return _classifier_instance
