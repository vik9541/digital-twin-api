"""
Улучшенный сервис аналитики расходов
"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ExpenseAnalytics:
    """Аналитика расходов"""
    
    # Категории товаров
    CATEGORIES = {
        'Продукты': ['молоко', 'хлеб', 'мясо', 'курица', 'рыба', 'овощи', 'фрукты', 
                     'яйца', 'сыр', 'масло', 'крупа', 'макароны', 'сахар', 'соль',
                     'йогурт', 'кефир', 'творог', 'колбаса', 'сосиски'],
        'Напитки': ['вода', 'сок', 'чай', 'кофе', 'молоко', 'кола', 'пепси', 'пиво', 'вино'],
        'Сладости': ['шоколад', 'конфеты', 'печенье', 'торт', 'пирожное', 'мороженое'],
        'Бытовая химия': ['порошок', 'мыло', 'шампунь', 'гель', 'моющее', 'чистящее'],
        'Гигиена': ['зубная', 'туалетная', 'салфетки', 'памперсы', 'прокладки'],
        'Лекарства': ['таблетки', 'витамины', 'лекарство', 'аспирин', 'парацетамол'],
        'Одежда': ['футболка', 'джинсы', 'куртка', 'обувь', 'носки'],
        'Электроника': ['телефон', 'наушники', 'зарядка', 'кабель', 'батарейки'],
        'Транспорт': ['бензин', 'метро', 'автобус', 'такси', 'парковка'],
        'Развлечения': ['кино', 'билет', 'игра', 'подписка'],
        'Рестораны': ['обед', 'ужин', 'кофе', 'бизнес-ланч']
    }
    
    def __init__(self, supabase_service):
        self.db = supabase_service
    
    async def get_monthly_stats(self, user_id: str, year: int = None, month: int = None) -> Dict:
        """Статистика за месяц"""
        if not year:
            year = date.today().year
        if not month:
            month = date.today().month
        
        # Получить чеки за месяц
        receipts = await self.db.get_user_receipts(user_id, limit=500)
        
        # Фильтрация по месяцу
        month_receipts = []
        for r in receipts:
            r_date = r.get('receipt_date') or r.get('created_at', '')
            if isinstance(r_date, str) and r_date:
                try:
                    dt = datetime.fromisoformat(r_date.replace('Z', '+00:00'))
                    if dt.year == year and dt.month == month:
                        month_receipts.append(r)
                except:
                    pass
        
        # Расчеты
        total = sum(r.get('total_sum', 0) for r in month_receipts)
        count = len(month_receipts)
        
        # По дням
        by_day = defaultdict(float)
        for r in month_receipts:
            r_date = r.get('receipt_date') or r.get('created_at', '')
            if r_date:
                day = r_date[:10]
                by_day[day] += r.get('total_sum', 0)
        
        # По категориям (из items)
        by_category = defaultdict(float)
        for r in month_receipts:
            for item in r.get('items', []):
                cat = item.get('category', 'Прочее')
                by_category[cat] += item.get('price', 0)
        
        return {
            'year': year,
            'month': month,
            'total': total,
            'count': count,
            'average': total / count if count else 0,
            'by_day': dict(sorted(by_day.items())),
            'by_category': dict(sorted(by_category.items(), key=lambda x: x[1], reverse=True)),
            'daily_average': total / 30 if total else 0
        }
    
    async def compare_periods(
        self, 
        user_id: str, 
        period1: Tuple[date, date],
        period2: Tuple[date, date]
    ) -> Dict:
        """Сравнение двух периодов"""
        
        receipts = await self.db.get_user_receipts(user_id, limit=1000)
        
        def filter_period(receipts, start, end):
            result = []
            for r in receipts:
                r_date = r.get('receipt_date') or r.get('created_at', '')
                if r_date:
                    try:
                        dt = datetime.fromisoformat(r_date.replace('Z', '+00:00')).date()
                        if start <= dt <= end:
                            result.append(r)
                    except:
                        pass
            return result
        
        p1_receipts = filter_period(receipts, period1[0], period1[1])
        p2_receipts = filter_period(receipts, period2[0], period2[1])
        
        p1_total = sum(r.get('total_sum', 0) for r in p1_receipts)
        p2_total = sum(r.get('total_sum', 0) for r in p2_receipts)
        
        diff = p2_total - p1_total
        diff_percent = (diff / p1_total * 100) if p1_total else 0
        
        return {
            'period1': {
                'start': str(period1[0]),
                'end': str(period1[1]),
                'total': p1_total,
                'count': len(p1_receipts)
            },
            'period2': {
                'start': str(period2[0]),
                'end': str(period2[1]),
                'total': p2_total,
                'count': len(p2_receipts)
            },
            'difference': diff,
            'difference_percent': diff_percent,
            'trend': 'up' if diff > 0 else 'down' if diff < 0 else 'stable'
        }
    
    async def get_top_expenses(self, user_id: str, days: int = 30, top_n: int = 10) -> List[Dict]:
        """Топ самых дорогих покупок"""
        
        receipts = await self.db.get_user_receipts(user_id, limit=500)
        
        cutoff = date.today() - timedelta(days=days)
        
        all_items = []
        for r in receipts:
            r_date = r.get('receipt_date') or r.get('created_at', '')
            if r_date:
                try:
                    dt = datetime.fromisoformat(r_date.replace('Z', '+00:00')).date()
                    if dt >= cutoff:
                        for item in r.get('items', []):
                            all_items.append({
                                'name': item.get('item_name', ''),
                                'price': item.get('price', 0),
                                'store': r.get('store_name', ''),
                                'date': str(dt)
                            })
                except:
                    pass
        
        # Сортировка по цене
        all_items.sort(key=lambda x: x['price'], reverse=True)
        
        return all_items[:top_n]
    
    async def detect_anomalies(self, user_id: str) -> List[Dict]:
        """Обнаружение аномальных трат"""
        
        stats = await self.get_monthly_stats(user_id)
        avg_check = stats.get('average', 0)
        
        if avg_check == 0:
            return []
        
        receipts = await self.db.get_user_receipts(user_id, limit=100)
        
        anomalies = []
        for r in receipts:
            total = r.get('total_sum', 0)
            # Аномалия - чек в 3 раза больше среднего
            if total > avg_check * 3:
                anomalies.append({
                    'date': r.get('receipt_date') or r.get('created_at', ''),
                    'store': r.get('store_name', ''),
                    'amount': total,
                    'average': avg_check,
                    'ratio': total / avg_check
                })
        
        return anomalies
    
    async def get_savings_recommendations(self, user_id: str) -> List[str]:
        """Рекомендации по экономии"""
        
        stats = await self.get_monthly_stats(user_id)
        recommendations = []
        
        by_category = stats.get('by_category', {})
        total = stats.get('total', 0)
        
        if total == 0:
            return ["📊 Недостаточно данных для анализа. Добавьте больше чеков!"]
        
        # Анализ категорий
        for cat, amount in by_category.items():
            percent = (amount / total) * 100
            
            if cat == 'Рестораны' and percent > 20:
                recommendations.append(
                    f"🍽️ Рестораны составляют {percent:.0f}% расходов. "
                    f"Готовка дома может сэкономить до 50%!"
                )
            
            if cat == 'Сладости' and percent > 10:
                recommendations.append(
                    f"🍬 Сладости - {percent:.0f}% бюджета. "
                    f"Сокращение поможет и кошельку, и здоровью!"
                )
            
            if cat == 'Напитки' and percent > 15:
                recommendations.append(
                    f"🥤 На напитки уходит {percent:.0f}%. "
                    f"Вода из фильтра - отличная альтернатива!"
                )
        
        # Общие рекомендации
        avg_check = stats.get('average', 0)
        if avg_check > 2000:
            recommendations.append(
                f"💡 Средний чек {avg_check:.0f}₽. "
                f"Попробуйте планировать покупки заранее!"
            )
        
        # Аномалии
        anomalies = await self.detect_anomalies(user_id)
        if anomalies:
            recommendations.append(
                f"⚠️ Обнаружено {len(anomalies)} аномально крупных покупок. "
                f"Стоит проверить необходимость таких трат."
            )
        
        if not recommendations:
            recommendations.append("✅ Ваши расходы выглядят сбалансированно!")
        
        return recommendations
    
    def format_monthly_report(self, stats: Dict) -> str:
        """Форматирование месячного отчета"""
        
        month_names = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }
        
        month_name = month_names.get(stats['month'], str(stats['month']))
        
        lines = [
            f"📊 **ОТЧЕТ ЗА {month_name.upper()} {stats['year']}**\n",
            f"💰 **Всего потрачено:** {stats['total']:.0f}₽",
            f"🧾 **Количество чеков:** {stats['count']}",
            f"📈 **Средний чек:** {stats['average']:.0f}₽",
            f"📅 **В среднем в день:** {stats['daily_average']:.0f}₽\n"
        ]
        
        # Топ категорий
        if stats.get('by_category'):
            lines.append("📦 **ПО КАТЕГОРИЯМ:**")
            for cat, amount in list(stats['by_category'].items())[:5]:
                percent = (amount / stats['total'] * 100) if stats['total'] else 0
                lines.append(f"  • {cat}: {amount:.0f}₽ ({percent:.0f}%)")
        
        return "\n".join(lines)
