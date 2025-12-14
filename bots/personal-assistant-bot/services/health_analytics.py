"""
Сервис аналитики здоровья
"""

from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict


class HealthAnalytics:
    """Аналитика данных о здоровье"""
    
    async def analyze_week(self, entries: List[Dict]) -> Dict:
        """
        Анализ записей за неделю
        
        Args:
            entries: Список записей из health_diary
        
        Returns:
            Словарь с аналитикой
        """
        analysis = {
            'food_count': 0,
            'activity_count': 0,
            'avg_sleep': None,
            'habits': {'good': 0, 'bad': 0},
            'by_day': defaultdict(list),
            'recommendations': []
        }
        
        sleep_hours = []
        
        for entry in entries:
            entry_type = entry.get('entry_type', '')
            data = entry.get('data', {})
            
            # Подсчет по типам
            if entry_type == 'food':
                analysis['food_count'] += 1
            elif entry_type == 'activity':
                analysis['activity_count'] += 1
            elif entry_type == 'sleep':
                hours = data.get('hours')
                if hours:
                    sleep_hours.append(hours)
            elif entry_type == 'habit':
                habit_type = data.get('type', 'good')
                analysis['habits'][habit_type] = analysis['habits'].get(habit_type, 0) + 1
            
            # Группировка по дням
            entry_date = entry.get('entry_date')
            if entry_date:
                analysis['by_day'][entry_date].append(entry)
        
        # Средний сон
        if sleep_hours:
            analysis['avg_sleep'] = sum(sleep_hours) / len(sleep_hours)
        
        # Рекомендации
        analysis['recommendations'] = self._generate_recommendations(analysis, len(entries))
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict, total_entries: int) -> List[str]:
        """Генерация рекомендаций на основе данных"""
        recommendations = []
        
        # Мало записей о питании
        if analysis['food_count'] < 7:  # Меньше 1 в день за неделю
            recommendations.append("📝 Записывай приемы пищи чаще для лучшего анализа")
        
        # Мало активности
        if analysis['activity_count'] < 3:
            recommendations.append("🏃 Добавь больше физической активности (хотя бы 3 раза в неделю)")
        
        # Проблемы со сном
        avg_sleep = analysis.get('avg_sleep')
        if avg_sleep:
            if avg_sleep < 7:
                recommendations.append("😴 Старайся спать минимум 7-8 часов")
            elif avg_sleep > 9:
                recommendations.append("⏰ Слишком много сна может быть признаком проблем")
        else:
            recommendations.append("😴 Начни отслеживать сон для анализа")
        
        # Вредные привычки
        bad_habits = analysis['habits'].get('bad', 0)
        if bad_habits > 0:
            recommendations.append(f"⚠️ За неделю {bad_habits} вредных привычек - постарайся сократить")
        
        # Мало записей вообще
        if total_entries < 7:
            recommendations.append("📊 Веди дневник активнее для точной аналитики")
        
        return recommendations
    
    async def analyze_patterns(self, entries: List[Dict], days: int = 30) -> Dict:
        """
        Анализ паттернов за период
        """
        patterns = {
            'most_active_day': None,
            'eating_times': [],
            'sleep_pattern': None,
            'habit_trend': None
        }
        
        # Группировка по дням недели
        by_weekday = defaultdict(int)
        eating_hours = []
        
        for entry in entries:
            entry_type = entry.get('entry_type', '')
            entry_time = entry.get('entry_time')
            created_at = entry.get('created_at')
            
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    by_weekday[dt.strftime('%A')] += 1
                    
                    if entry_type == 'food' and entry_time:
                        hour = int(entry_time.split(':')[0])
                        eating_hours.append(hour)
                except:
                    pass
        
        # Самый активный день
        if by_weekday:
            patterns['most_active_day'] = max(by_weekday, key=by_weekday.get)
        
        # Время приема пищи
        if eating_hours:
            avg_hour = sum(eating_hours) / len(eating_hours)
            patterns['eating_times'] = {
                'average_hour': int(avg_hour),
                'earliest': min(eating_hours),
                'latest': max(eating_hours)
            }
        
        return patterns
    
    async def get_health_score(self, entries: List[Dict]) -> int:
        """
        Рассчитать "счет здоровья" (0-100)
        """
        score = 50  # Базовый счет
        
        week_analysis = await self.analyze_week(entries)
        
        # Питание (+10 за регулярность)
        if week_analysis['food_count'] >= 14:  # 2 раза в день
            score += 10
        elif week_analysis['food_count'] >= 7:
            score += 5
        
        # Активность (+15 за регулярность)
        if week_analysis['activity_count'] >= 5:
            score += 15
        elif week_analysis['activity_count'] >= 3:
            score += 10
        elif week_analysis['activity_count'] >= 1:
            score += 5
        
        # Сон (+15 за оптимальное количество)
        avg_sleep = week_analysis.get('avg_sleep')
        if avg_sleep:
            if 7 <= avg_sleep <= 9:
                score += 15
            elif 6 <= avg_sleep <= 10:
                score += 10
            else:
                score += 5
        
        # Штраф за вредные привычки
        bad_habits = week_analysis['habits'].get('bad', 0)
        score -= min(bad_habits * 5, 20)  # Максимум -20
        
        return max(0, min(100, score))
