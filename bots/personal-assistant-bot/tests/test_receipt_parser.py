"""
Тесты для парсера чеков
"""

import pytest
from services.receipt_parser import ReceiptParser


class TestReceiptParser:
    """Тесты парсера чеков"""
    
    def setup_method(self):
        self.parser = ReceiptParser()
    
    def test_detect_store_pyaterochka(self):
        """Тест определения Пятёрочки"""
        texts = ['ПЯТЕРОЧКА', 'X5 Retail', 'пятёрочка']
        
        for text in texts:
            store = self.parser.detect_store(text)
            assert store == 'Пятёрочка', f"Failed for: {text}"
    
    def test_detect_store_magnit(self):
        """Тест определения Магнита"""
        texts = ['МАГНИТ', 'АО ТАНДЕР']
        
        for text in texts:
            store = self.parser.detect_store(text)
            assert store == 'Магнит'
    
    def test_detect_store_unknown(self):
        """Тест неизвестного магазина"""
        store = self.parser.detect_store("Какой-то магазин")
        assert store == 'Неизвестный магазин'
    
    def test_extract_items_simple(self):
        """Тест извлечения товаров"""
        text = """
        Молоко 2.5% 1л    89.90
        Хлеб белый        45.00
        Яйца С1 10шт      85.00
        """
        
        items = self.parser.extract_items(text)
        
        # Должны найти товары
        assert len(items) > 0
        
        # Проверить что есть цены
        for item in items:
            assert 'name' in item
            assert 'price' in item
    
    def test_extract_total(self):
        """Тест извлечения итоговой суммы"""
        texts = [
            ('ИТОГО: 1234.56', 1234.56),
            ('ИТОГО=1500.00', 1500.00),
            ('ВСЕГО: 999', 999.0),
            ('К ОПЛАТЕ 500.50', 500.50),
        ]
        
        for text, expected in texts:
            total = self.parser.extract_total(text)
            assert total == expected, f"Failed for: {text}"
    
    def test_extract_date(self):
        """Тест извлечения даты"""
        texts = [
            '13.12.2025 15:30',
            '13/12/2025',
            '2025-12-13',
        ]
        
        for text in texts:
            date = self.parser.extract_date(text)
            assert date is not None, f"Failed for: {text}"
    
    def test_categorize_item_food(self):
        """Тест категоризации продуктов"""
        items = ['Молоко', 'Хлеб', 'Мясо говядины', 'Яйца куриные']
        
        for item in items:
            category = self.parser.categorize_item(item)
            assert category == 'Продукты', f"Failed for: {item}"
    
    def test_categorize_item_drinks(self):
        """Тест категоризации напитков"""
        items = ['Сок апельсиновый', 'Кофе молотый', 'Чай черный']
        
        for item in items:
            category = self.parser.categorize_item(item)
            assert category == 'Напитки', f"Failed for: {item}"
    
    def test_categorize_item_unknown(self):
        """Тест неизвестной категории"""
        category = self.parser.categorize_item("Что-то непонятное XYZ123")
        assert category == 'Прочее'
    
    def test_parse_receipt_full(self):
        """Полный тест парсинга чека"""
        text = """
        ООО "АГРОТОРГ"
        ИНН 7825706086
        ПЯТЕРОЧКА #1234
        
        Молоко 2.5% 1л      89.90
        Хлеб нарезной       45.00
        
        ИТОГО: 134.90
        
        13.12.2025 14:30
        """
        
        result = self.parser.parse(text)
        
        assert result['store_name'] == 'Пятёрочка'
        assert result['total_sum'] == 134.90
        assert len(result['items']) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
