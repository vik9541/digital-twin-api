"""
Сервис сравнения цен через Yandex Market API
"""

import os
import aiohttp
from typing import List, Dict, Optional


class MarketService:
    """Сервис для сравнения цен в маркетплейсах"""
    
    def __init__(self):
        self.yandex_token = os.getenv('YANDEX_MARKET_API_KEY')
        self.base_url = "https://api.market.yandex.ru/v2"
    
    async def find_cheaper_items(self, items: List[Dict]) -> List[Dict]:
        """
        Найти товары дешевле в других магазинах
        
        Args:
            items: Список товаров с ценами из чека
        
        Returns:
            Список товаров с более дешевыми альтернативами
        """
        if not self.yandex_token:
            # Fallback: использовать mock данные для демонстрации
            return await self._mock_cheaper_items(items)
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            for item in items[:5]:  # Ограничиваем количество запросов
                cheaper = await self._search_item(session, item)
                if cheaper:
                    results.append(cheaper)
        
        return results
    
    async def _search_item(self, session: aiohttp.ClientSession, item: Dict) -> Optional[Dict]:
        """Поиск товара в Yandex Market"""
        try:
            params = {
                'text': item['name'],
                'count': 5
            }
            
            headers = {
                'Authorization': f'OAuth {self.yandex_token}'
            }
            
            async with session.get(
                f"{self.base_url}/search",
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                results = data.get('search', {}).get('results', [])
                if not results:
                    return None
                
                # Найти самый дешевый
                cheapest = min(
                    results,
                    key=lambda x: x.get('price', {}).get('value', float('inf'))
                )
                
                cheapest_price = cheapest.get('price', {}).get('value', 0)
                
                if cheapest_price and cheapest_price < item.get('price', 0):
                    return {
                        'item_name': item['name'],
                        'original_price': item['price'],
                        'cheaper_price': cheapest_price,
                        'savings': item['price'] - cheapest_price,
                        'store': cheapest.get('shop', {}).get('name', 'Yandex Market'),
                        'url': cheapest.get('url')
                    }
                
        except Exception as e:
            print(f"Ошибка поиска {item['name']}: {e}")
        
        return None
    
    async def _mock_cheaper_items(self, items: List[Dict]) -> List[Dict]:
        """
        Mock данные для демонстрации (когда API недоступен)
        """
        mock_savings = []
        
        # Симулируем экономию для некоторых товаров
        import random
        
        for item in items[:3]:
            if random.random() > 0.5:  # 50% шанс найти дешевле
                original = item.get('price', 100)
                discount = random.uniform(0.1, 0.3)  # 10-30% экономия
                cheaper = round(original * (1 - discount), 2)
                
                stores = ['Ozon', 'Wildberries', 'Яндекс.Маркет', 'СберМегаМаркет']
                
                mock_savings.append({
                    'item_name': item['name'],
                    'original_price': original,
                    'cheaper_price': cheaper,
                    'savings': round(original - cheaper, 2),
                    'store': random.choice(stores),
                    'url': None
                })
        
        return mock_savings
    
    async def get_price_history(self, item_name: str) -> Optional[Dict]:
        """
        Получить историю цен на товар (заглушка)
        """
        # TODO: Реализовать когда будет API
        return None
    
    async def find_best_store(self, item_name: str, location: str = None) -> Optional[Dict]:
        """
        Найти лучший магазин для покупки товара
        """
        # TODO: Реализовать когда будет API
        return None
