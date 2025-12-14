"""
Парсер чеков - извлечение структурированных данных из текста чека
"""

import re
from typing import Dict, List, Optional
from datetime import datetime


class ReceiptParser:
    """Парсер для извлечения данных из текста чека"""
    
    # Известные магазины
    KNOWN_STORES = {
        'пятёрочка': 'Пятёрочка',
        'пятерочка': 'Пятёрочка',
        'x5': 'Пятёрочка',
        'перекресток': 'Перекрёсток',
        'перекрёсток': 'Перекрёсток',
        'магнит': 'Магнит',
        'magnit': 'Магнит',
        'дикси': 'Дикси',
        'dixy': 'Дикси',
        'ашан': 'Ашан',
        'auchan': 'Ашан',
        'метро': 'Метро',
        'metro': 'Метро',
        'окей': 'О'Кей',
        'okey': 'О'Кей',
        'лента': 'Лента',
        'lenta': 'Лента',
        'вкусвилл': 'ВкусВилл',
        'вкусвil': 'ВкусВилл',
        'красное белое': 'Красное & Белое',
        'бристоль': 'Бристоль',
        'fix price': 'Fix Price',
        'фикс прайс': 'Fix Price',
        'азбука вкуса': 'Азбука Вкуса',
        'маршал': 'Маршал',
        'globus': 'Глобус',
        'глобус': 'Глобус',
        'spar': 'Spar',
        'спар': 'Spar',
        'билла': 'Билла',
        'billa': 'Билла',
    }
    
    # Категории товаров
    CATEGORIES = {
        'Молочка': ['молоко', 'кефир', 'йогурт', 'творог', 'сметана', 'сыр', 
                   'масло сливочное', 'ряженка', 'простокваша', 'сливки'],
        'Мясо': ['курица', 'куриц', 'филе', 'грудка', 'говядина', 'свинина',
                'фарш', 'колбаса', 'сосиски', 'ветчина', 'бекон', 'индейка'],
        'Рыба': ['рыба', 'лосось', 'сёмга', 'форель', 'треска', 'минтай',
                'сельдь', 'скумбрия', 'креветки', 'кальмар'],
        'Хлеб': ['хлеб', 'батон', 'булка', 'багет', 'лаваш', 'питa'],
        'Овощи': ['помидор', 'томат', 'огурец', 'картофель', 'картошка', 
                 'морковь', 'лук', 'капуста', 'перец', 'баклажан', 'кабачок',
                 'свекла', 'редис', 'чеснок', 'салат', 'зелень', 'укроп', 'петрушка'],
        'Фрукты': ['яблоко', 'яблок', 'банан', 'апельсин', 'мандарин', 'груша',
                  'виноград', 'лимон', 'киви', 'ананас', 'персик', 'слива',
                  'абрикос', 'арбуз', 'дыня', 'гранат'],
        'Напитки': ['вода', 'сок', 'лимонад', 'кола', 'coca', 'pepsi', 'fanta',
                   'sprite', 'чай', 'кофе', 'компот', 'морс', 'квас',
                   'напиток', 'энергетик', 'газировка'],
        'Алкоголь': ['пиво', 'вино', 'водка', 'виски', 'коньяк', 'ром', 'джин',
                    'шампанское', 'beer', 'wine'],
        'Крупы': ['рис', 'гречка', 'овсянка', 'пшено', 'перловка', 'манка',
                 'макароны', 'спагетти', 'лапша', 'мука', 'крупа'],
        'Сладости': ['шоколад', 'конфет', 'печенье', 'торт', 'пирожное',
                    'мороженое', 'вафли', 'зефир', 'мармелад', 'халва'],
        'Снеки': ['чипсы', 'сухарики', 'орехи', 'семечки', 'попкорн', 'крекер'],
        'Бытовая химия': ['порошок', 'моющее', 'шампунь', 'мыло', 'гель',
                         'зубная', 'туалетная', 'салфетки', 'памперсы', 'прокладки'],
    }
    
    async def parse_receipt_text(self, text: str) -> Dict:
        """
        Парсит текст чека и извлекает структурированные данные
        
        Args:
            text: Распознанный текст чека
        
        Returns:
            Словарь с данными чека
        """
        return {
            'store_name': self._extract_store_name(text),
            'receipt_date': self._extract_date(text),
            'receipt_time': self._extract_time(text),
            'items': self._extract_items(text),
            'total_sum': self._extract_total(text),
            'address': self._extract_address(text),
            'raw_text': text
        }
    
    def _extract_store_name(self, text: str) -> str:
        """Извлечь название магазина"""
        text_lower = text.lower()
        
        for keyword, store_name in self.KNOWN_STORES.items():
            if keyword in text_lower:
                return store_name
        
        # Попробовать первую строку как название
        lines = text.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 50 and first_line:  # Разумная длина для названия
                return first_line
        
        return 'Неизвестный магазин'
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Извлечь дату из чека"""
        # Паттерны даты
        patterns = [
            r'(\d{2}[./]\d{2}[./]\d{4})',  # 13.12.2025 или 13/12/2025
            r'(\d{2}[./]\d{2}[./]\d{2})',   # 13.12.25
            r'(\d{4}-\d{2}-\d{2})',          # 2025-12-13
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1)
                # Нормализовать формат
                date_str = date_str.replace('/', '.')
                return date_str
        
        return None
    
    def _extract_time(self, text: str) -> Optional[str]:
        """Извлечь время из чека"""
        pattern = r'(\d{2}:\d{2}(?::\d{2})?)'
        match = re.search(pattern, text)
        return match.group(1) if match else None
    
    def _extract_items(self, text: str) -> List[Dict]:
        """Извлечь список товаров и цен"""
        items = []
        
        # Паттерны для товаров с ценами
        patterns = [
            # "Товар    123.45" или "Товар 123,45"
            r'^(.+?)\s+(\d+[.,]\d{2})\s*$',
            # "Товар * 2 = 246.90"
            r'^(.+?)\s*\*\s*\d+\s*=\s*(\d+[.,]\d{2})',
            # "123.45 Товар"
            r'^(\d+[.,]\d{2})\s+(.+?)$',
        ]
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Пропустить строки с итогом
            if any(skip in line.lower() for skip in ['итого', 'total', 'сумма', 'всего', 'оплачено', 'наличными', 'картой']):
                continue
            
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    # Определить что название, что цена
                    if groups[0].replace(',', '.').replace('.', '').isdigit():
                        price_str = groups[0]
                        item_name = groups[1]
                    else:
                        item_name = groups[0]
                        price_str = groups[1]
                    
                    # Очистить название
                    item_name = self._clean_item_name(item_name)
                    
                    if len(item_name) < 2:  # Слишком короткое название
                        continue
                    
                    try:
                        price = float(price_str.replace(',', '.'))
                        
                        # Фильтр нереальных цен
                        if 0.5 <= price <= 100000:
                            items.append({
                                'name': item_name,
                                'price': price,
                                'category': self._categorize_item(item_name)
                            })
                    except ValueError:
                        continue
                    
                    break
        
        return items
    
    def _clean_item_name(self, name: str) -> str:
        """Очистить название товара"""
        # Удалить лишние символы
        name = re.sub(r'[*#@%&!]+', '', name)
        # Удалить множественные пробелы
        name = re.sub(r'\s+', ' ', name)
        # Убрать количество в начале/конце
        name = re.sub(r'^\d+\s*[xх*]\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*\d+\s*(шт|кг|г|л|мл)\.?\s*$', '', name, flags=re.IGNORECASE)
        
        return name.strip()
    
    def _categorize_item(self, item_name: str) -> str:
        """Определить категорию товара"""
        item_lower = item_name.lower()
        
        for category, keywords in self.CATEGORIES.items():
            if any(keyword in item_lower for keyword in keywords):
                return category
        
        return 'Прочее'
    
    def _extract_total(self, text: str) -> float:
        """Извлечь итоговую сумму"""
        # Паттерны для итога
        patterns = [
            r'итого[:\s]+(\d+[.,]\d{2})',
            r'total[:\s]+(\d+[.,]\d{2})',
            r'сумма[:\s]+(\d+[.,]\d{2})',
            r'всего[:\s]+(\d+[.,]\d{2})',
            r'к\s*оплате[:\s]+(\d+[.,]\d{2})',
            r'оплачено[:\s]+(\d+[.,]\d{2})',
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    return float(match.group(1).replace(',', '.'))
                except ValueError:
                    continue
        
        return 0.0
    
    def _extract_address(self, text: str) -> Optional[str]:
        """Извлечь адрес магазина"""
        patterns = [
            r'(?:ул\.?|улица)\s*([\w\s.,]+?)(?:\d|$)',
            r'(?:пр\.?|проспект)\s*([\w\s.,]+?)(?:\d|$)',
            r'г\.\s*(\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
