"""
Обработчик дневника здоровья
"""

from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta

from services.supabase_service import SupabaseService
from services.health_analytics import HealthAnalytics


class HealthHandler:
    """Обработчик дневника здоровья"""
    
    def __init__(self):
        self.db = SupabaseService()
        self.analytics = HealthAnalytics()
    
    async def handle_health_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Обработать сообщение как запись в дневник здоровья.
        Возвращает True если сообщение обработано.
        """
        text = update.message.text
        if not text:
            return False
        
        # Определить тип записи
        entry_type, data = self._parse_health_entry(text)
        
        if entry_type is None:
            return False  # Не похоже на запись о здоровье
        
        user_id = str(update.effective_user.id)
        
        # Сохранить в БД
        await self.db.save_health_entry(
            user_id=user_id,
            entry_type=entry_type,
            description=text,
            data=data
        )
        
        # Ответить подтверждением
        emoji_map = {
            'food': '🍽️',
            'activity': '🏃',
            'habit': '🧘',
            'sleep': '😴',
            'mood': '😊',
            'measurement': '📏'
        }
        
        emoji = emoji_map.get(entry_type, '📝')
        category = {
            'food': 'Питание',
            'activity': 'Активность',
            'habit': 'Привычка',
            'sleep': 'Сон',
            'mood': 'Настроение',
            'measurement': 'Измерение'
        }.get(entry_type, 'Запись')
        
        await update.message.reply_text(f"{emoji} Записано в дневник: {category}")
        return True
    
    def _parse_health_entry(self, text: str) -> tuple:
        """
        Определить тип записи и извлечь данные.
        Возвращает (entry_type, data) или (None, None)
        """
        text_lower = text.lower()
        
        # Еда
        food_keywords = ['съел', 'съела', 'выпил', 'выпила', 'поел', 'поела', 
                        'попил', 'попила', 'завтрак', 'обед', 'ужин', 'перекус']
        if any(kw in text_lower for kw in food_keywords):
            return 'food', {'description': text}
        
        # Сон
        sleep_keywords = ['спал', 'спала', 'проснул', 'проснулась', 'лег спать', 
                         'легла спать', 'сон', 'выспал']
        if any(kw in text_lower for kw in sleep_keywords):
            # Попробовать извлечь часы
            import re
            hours_match = re.search(r'(\d+)\s*час', text_lower)
            hours = int(hours_match.group(1)) if hours_match else None
            return 'sleep', {'description': text, 'hours': hours}
        
        # Активность
        activity_keywords = ['пошел', 'пошла', 'побегал', 'побегала', 'занимался', 
                            'занималась', 'тренировка', 'пробежал', 'пробежала',
                            'проехал', 'проехала', 'прошел', 'прошла', 'велосипед',
                            'бег', 'йога', 'плавал', 'плавала', 'зал']
        if any(kw in text_lower for kw in activity_keywords):
            return 'activity', {'description': text}
        
        # Вредные привычки
        habit_keywords = ['курил', 'курила', 'покурил', 'покурила', 'сигарет',
                         'выпил алкоголь', 'выпила алкоголь', 'пиво', 'вино', 'водк']
        if any(kw in text_lower for kw in habit_keywords):
            return 'habit', {'description': text, 'type': 'bad'}
        
        # Настроение
        mood_keywords = ['настроение', 'чувствую', 'устал', 'устала', 
                        'энергия', 'бодр', 'сонный', 'сонная']
        if any(kw in text_lower for kw in mood_keywords):
            return 'mood', {'description': text}
        
        # Измерения
        measurement_keywords = ['вес', 'давление', 'пульс', 'температура', 'кг', 'мм']
        if any(kw in text_lower for kw in measurement_keywords):
            return 'measurement', {'description': text}
        
        return None, None
    
    async def health_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отчет о здоровье за день /health report"""
        user_id = str(update.effective_user.id)
        
        # Получить записи за сегодня
        entries = await self.db.get_health_entries(user_id, days=1)
        
        if not entries:
            await update.message.reply_text(
                "📊 **ОТЧЕТ О ЗДОРОВЬЕ**\n\n"
                "Записей за сегодня нет.\n\n"
                "_Просто напиши что съел или сделал, и я запишу!_",
                parse_mode='Markdown'
            )
            return
        
        message = "📊 **ОТЧЕТ О ЗДОРОВЬЕ (Сегодня)**\n\n"
        
        # Группировать по типам
        by_type = {}
        for entry in entries:
            entry_type = entry['entry_type']
            if entry_type not in by_type:
                by_type[entry_type] = []
            by_type[entry_type].append(entry)
        
        # Питание
        if 'food' in by_type:
            message += "🍽️ **ПИТАНИЕ:**\n"
            for item in by_type['food']:
                time = item.get('entry_time', '')[:5] if item.get('entry_time') else ''
                desc = item.get('description', '')
                message += f"• {time} {desc}\n"
            message += "\n"
        
        # Активность
        if 'activity' in by_type:
            message += "🏃 **АКТИВНОСТЬ:**\n"
            for item in by_type['activity']:
                message += f"• {item.get('description', '')}\n"
            message += "\n"
        
        # Сон
        if 'sleep' in by_type:
            message += "😴 **СОН:**\n"
            for item in by_type['sleep']:
                hours = item.get('data', {}).get('hours')
                if hours:
                    message += f"• {hours} часов\n"
                else:
                    message += f"• {item.get('description', '')}\n"
            message += "\n"
        
        # Привычки
        if 'habit' in by_type:
            message += "🧘 **ПРИВЫЧКИ:**\n"
            for item in by_type['habit']:
                message += f"• {item.get('description', '')}\n"
            message += "\n"
        
        # Настроение
        if 'mood' in by_type:
            message += "😊 **НАСТРОЕНИЕ:**\n"
            for item in by_type['mood']:
                message += f"• {item.get('description', '')}\n"
            message += "\n"
        
        # Измерения
        if 'measurement' in by_type:
            message += "📏 **ИЗМЕРЕНИЯ:**\n"
            for item in by_type['measurement']:
                message += f"• {item.get('description', '')}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def health_week(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отчет о здоровье за неделю /health week"""
        user_id = str(update.effective_user.id)
        
        entries = await self.db.get_health_entries(user_id, days=7)
        
        if not entries:
            await update.message.reply_text("📊 Записей за неделю нет")
            return
        
        # Аналитика
        analysis = await self.analytics.analyze_week(entries)
        
        message = "📊 **ОТЧЕТ ЗА НЕДЕЛЮ**\n\n"
        
        message += f"📝 Всего записей: {len(entries)}\n\n"
        
        if analysis.get('food_count'):
            message += f"🍽️ Приемов пищи: {analysis['food_count']}\n"
        
        if analysis.get('activity_count'):
            message += f"🏃 Активностей: {analysis['activity_count']}\n"
        
        if analysis.get('avg_sleep'):
            message += f"😴 Средний сон: {analysis['avg_sleep']:.1f} часов\n"
        
        if analysis.get('habits'):
            bad_habits = analysis['habits'].get('bad', 0)
            if bad_habits > 0:
                message += f"⚠️ Вредных привычек: {bad_habits}\n"
        
        # Рекомендации
        if analysis.get('recommendations'):
            message += "\n💡 **РЕКОМЕНДАЦИИ:**\n"
            for rec in analysis['recommendations']:
                message += f"• {rec}\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
