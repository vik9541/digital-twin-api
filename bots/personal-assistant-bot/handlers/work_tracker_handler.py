"""
Work Tracker Handler - обработчик учёта рабочего времени
Команды: /work, "пришёл на работу", "ушёл с работы"
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, Any, List
from telegram import Update
from telegram.ext import ContextTypes
from utils.timezone import now as moscow_now, MOSCOW_TZ
import logging

logger = logging.getLogger(__name__)


class WorkTrackerHandler:
    """Обработчик учёта рабочего времени"""
    
    LOG_TYPES = {
        "arrival": "🏢 Приход",
        "departure": "🏠 Уход",
        "break_start": "☕ Начало перерыва",
        "break_end": "💪 Конец перерыва",
        "overtime": "🔥 Переработка"
    }
    
    def __init__(self, supabase_service):
        self.db = supabase_service
    
    # ========== Основные методы ==========
    
    async def log_arrival(self, user_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Записать приход на работу"""
        return await self._add_log(user_id, "arrival", notes)
    
    async def log_departure(self, user_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Записать уход с работы"""
        return await self._add_log(user_id, "departure", notes)
    
    async def log_break_start(self, user_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Записать начало перерыва"""
        return await self._add_log(user_id, "break_start", notes)
    
    async def log_break_end(self, user_id: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Записать конец перерыва"""
        return await self._add_log(user_id, "break_end", notes)
    
    async def _add_log(
        self, 
        user_id: str, 
        log_type: str, 
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Добавить запись в лог рабочего времени"""
        now = moscow_now()
        
        data = {
            "user_id": user_id,
            "log_type": log_type,
            "log_time": now.strftime("%H:%M:%S"),
            "log_date": now.strftime("%Y-%m-%d"),
            "notes": notes,
            "created_at": now.isoformat()
        }
        
        try:
            result = self.db.client.table("work_logs").insert(data).execute()
            logger.info(f"Work log added: {log_type} for user {user_id} at {now}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Error adding work log: {e}")
            return {}
    
    # ========== Статистика ==========
    
    async def get_today_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """Получить логи за сегодня"""
        today = date.today().isoformat()
        
        try:
            result = self.db.client.table("work_logs") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("log_date", today) \
                .order("log_time") \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting today logs: {e}")
            return []
    
    async def get_logs_for_date(self, user_id: str, target_date: date) -> List[Dict[str, Any]]:
        """Получить логи за конкретную дату"""
        try:
            result = self.db.client.table("work_logs") \
                .select("*") \
                .eq("user_id", user_id) \
                .eq("log_date", target_date.isoformat()) \
                .order("log_time") \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting logs for date: {e}")
            return []
    
    async def get_week_logs(self, user_id: str) -> List[Dict[str, Any]]:
        """Получить логи за последнюю неделю"""
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        
        try:
            result = self.db.client.table("work_logs") \
                .select("*") \
                .eq("user_id", user_id) \
                .gte("log_date", week_ago) \
                .order("log_date", desc=True) \
                .order("log_time") \
                .execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting week logs: {e}")
            return []
    
    async def calculate_work_hours(self, user_id: str, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Рассчитать рабочие часы за день"""
        if target_date is None:
            target_date = date.today()
        
        logs = await self.get_logs_for_date(user_id, target_date)
        
        if not logs:
            return {"hours": 0, "minutes": 0, "status": "no_data"}
        
        arrival_time = None
        departure_time = None
        break_minutes = 0
        current_break_start = None
        
        for log in logs:
            log_type = log.get("log_type")
            log_time = log.get("log_time")
            
            if log_type == "arrival" and arrival_time is None:
                arrival_time = self._parse_time(log_time)
            elif log_type == "departure":
                departure_time = self._parse_time(log_time)
            elif log_type == "break_start":
                current_break_start = self._parse_time(log_time)
            elif log_type == "break_end" and current_break_start:
                break_end = self._parse_time(log_time)
                delta = (break_end.hour * 60 + break_end.minute) - (current_break_start.hour * 60 + current_break_start.minute)
                break_minutes += delta
                current_break_start = None
        
        # Если нет ухода, считаем до текущего времени
        if arrival_time and not departure_time:
            now = moscow_now()
            if target_date == date.today():
                departure_time = now.time()
                status = "in_progress"
            else:
                status = "incomplete"
                return {"hours": 0, "minutes": 0, "status": status}
        elif arrival_time and departure_time:
            status = "completed"
        else:
            return {"hours": 0, "minutes": 0, "status": "no_arrival"}
        
        # Расчёт
        arrival_minutes = arrival_time.hour * 60 + arrival_time.minute
        departure_minutes = departure_time.hour * 60 + departure_time.minute
        
        total_minutes = departure_minutes - arrival_minutes - break_minutes
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        return {
            "hours": hours,
            "minutes": minutes,
            "total_minutes": total_minutes,
            "break_minutes": break_minutes,
            "arrival": arrival_time.strftime("%H:%M"),
            "departure": departure_time.strftime("%H:%M") if status == "completed" else "сейчас",
            "status": status
        }
    
    def _parse_time(self, time_str: str) -> time:
        """Парсинг времени из строки"""
        parts = time_str.split(":")
        return datetime.strptime(time_str[:8] if len(time_str) > 8 else time_str, "%H:%M:%S").time()
    
    # ========== Форматирование ==========
    
    def format_log(self, log: Dict[str, Any]) -> str:
        """Форматировать запись"""
        log_type = log.get("log_type", "unknown")
        log_time = log.get("log_time", "")[:5]  # HH:MM
        notes = log.get("notes", "")
        
        type_name = self.LOG_TYPES.get(log_type, log_type)
        result = f"{type_name} в {log_time}"
        
        if notes:
            result += f" ({notes})"
        
        return result
    
    def format_day_summary(self, logs: List[Dict[str, Any]], work_hours: Dict[str, Any]) -> str:
        """Форматировать сводку за день"""
        if not logs:
            return "📭 Записей за сегодня нет"
        
        lines = ["📊 **Рабочий день:**\n"]
        
        for log in logs:
            lines.append(f"  • {self.format_log(log)}")
        
        lines.append("")
        
        status = work_hours.get("status")
        hours = work_hours.get("hours", 0)
        minutes = work_hours.get("minutes", 0)
        
        if status == "in_progress":
            lines.append(f"⏱ **На работе уже:** {hours}ч {minutes}м")
        elif status == "completed":
            lines.append(f"✅ **Отработано:** {hours}ч {minutes}м")
            if work_hours.get("break_minutes"):
                lines.append(f"☕ **Перерыв:** {work_hours['break_minutes']}м")
        elif status == "no_arrival":
            lines.append("⚠️ Нет отметки о приходе")
        
        return "\n".join(lines)
    
    def format_week_report(self, logs: List[Dict[str, Any]], user_id: str) -> str:
        """Форматировать недельный отчёт"""
        if not logs:
            return "📭 Записей за неделю нет"
        
        # Группируем по дням
        days = {}
        for log in logs:
            log_date = log.get("log_date")
            if log_date not in days:
                days[log_date] = []
            days[log_date].append(log)
        
        lines = ["📊 **Отчёт за неделю:**\n"]
        total_hours = 0
        total_minutes = 0
        work_days = 0
        
        for day_date in sorted(days.keys(), reverse=True):
            day_logs = days[day_date]
            
            # Парсим дату
            dt = datetime.strptime(day_date, "%Y-%m-%d")
            day_name = self._get_day_name(dt.weekday())
            
            # Находим приход и уход
            arrival = None
            departure = None
            for log in day_logs:
                if log.get("log_type") == "arrival" and not arrival:
                    arrival = log.get("log_time", "")[:5]
                elif log.get("log_type") == "departure":
                    departure = log.get("log_time", "")[:5]
            
            if arrival:
                work_days += 1
                if departure:
                    lines.append(f"📅 {day_date} ({day_name}): {arrival} - {departure}")
                else:
                    lines.append(f"📅 {day_date} ({day_name}): {arrival} - ?")
        
        lines.append(f"\n📈 **Рабочих дней:** {work_days}")
        
        return "\n".join(lines)
    
    def _get_day_name(self, weekday: int) -> str:
        """Название дня недели"""
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        return days[weekday]
    
    # ========== Обработчики команд ==========
    
    async def handle_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /work"""
        user_id = str(update.effective_user.id)
        args = context.args if context.args else []
        
        if not args:
            # Показать статус
            await self._show_status(update, user_id)
            return
        
        action = args[0].lower()
        notes = " ".join(args[1:]) if len(args) > 1 else None
        
        if action in ["приход", "пришёл", "пришел", "arrival", "in"]:
            result = await self.log_arrival(user_id, notes)
            await update.message.reply_text(
                f"🏢 Приход отмечен в {moscow_now().strftime('%H:%M')}\nУдачного рабочего дня! 💪"
            )
        elif action in ["уход", "ушёл", "ушел", "departure", "out"]:
            result = await self.log_departure(user_id, notes)
            work_hours = await self.calculate_work_hours(user_id)
            hours = work_hours.get("hours", 0)
            minutes = work_hours.get("minutes", 0)
            await update.message.reply_text(
                f"🏠 Уход отмечен в {moscow_now().strftime('%H:%M')}\n"
                f"✅ Отработано: {hours}ч {minutes}м\nХорошего отдыха! 🌙"
            )
        elif action in ["перерыв", "обед", "break"]:
            result = await self.log_break_start(user_id, notes)
            await update.message.reply_text("☕ Приятного перерыва!")
        elif action in ["вернулся", "назад", "back"]:
            result = await self.log_break_end(user_id, notes)
            await update.message.reply_text("💪 С возвращением! Продолжаем работать.")
        elif action in ["статус", "status"]:
            await self._show_status(update, user_id)
        elif action in ["неделя", "week", "отчёт", "отчет", "report"]:
            await self._show_week_report(update, user_id)
        else:
            await update.message.reply_text(
                "📋 **Команды:**\n"
                "/work приход — отметить приход\n"
                "/work уход — отметить уход\n"
                "/work перерыв — начать перерыв\n"
                "/work вернулся — закончить перерыв\n"
                "/work статус — статус сегодня\n"
                "/work отчёт — отчёт за неделю"
            )
    
    async def _show_status(self, update: Update, user_id: str) -> None:
        """Показать статус за сегодня"""
        logs = await self.get_today_logs(user_id)
        work_hours = await self.calculate_work_hours(user_id)
        summary = self.format_day_summary(logs, work_hours)
        await update.message.reply_text(summary, parse_mode="Markdown")
    
    async def _show_week_report(self, update: Update, user_id: str) -> None:
        """Показать отчёт за неделю"""
        logs = await self.get_week_logs(user_id)
        report = self.format_week_report(logs, user_id)
        await update.message.reply_text(report, parse_mode="Markdown")
    
    # ========== Обработка естественного языка ==========
    
    async def handle_natural(self, user_id: str, text: str) -> Optional[str]:
        """Обработать запрос на естественном языке"""
        text_lower = text.lower()
        
        # Приход
        if any(phrase in text_lower for phrase in [
            "пришёл на работу", "пришел на работу", "пришла на работу",
            "я на работе", "приступил к работе", "начал работать"
        ]):
            await self.log_arrival(user_id)
            return f"🏢 Приход отмечен в {moscow_now().strftime('%H:%M')}!\nУдачного рабочего дня! 💪"
        
        # Уход
        if any(phrase in text_lower for phrase in [
            "ушёл с работы", "ушел с работы", "ушла с работы",
            "ухожу с работы", "домой иду", "иду домой", "закончил работу"
        ]):
            await self.log_departure(user_id)
            work_hours = await self.calculate_work_hours(user_id)
            hours = work_hours.get("hours", 0)
            minutes = work_hours.get("minutes", 0)
            return (
                f"🏠 Уход отмечен в {moscow_now().strftime('%H:%M')}!\n"
                f"✅ Сегодня отработано: {hours}ч {minutes}м\nХорошего отдыха! 🌙"
            )
        
        # Перерыв
        if any(phrase in text_lower for phrase in [
            "ушёл на обед", "ушел на обед", "ушла на обед", "на обеде", "перерыв"
        ]):
            await self.log_break_start(user_id)
            return "☕ Приятного перерыва!"
        
        # Конец перерыва
        if any(phrase in text_lower for phrase in [
            "вернулся с обеда", "вернулась с обеда", "конец перерыва"
        ]):
            await self.log_break_end(user_id)
            return "💪 С возвращением! Продолжаем работать."
        
        # Статус
        if any(phrase in text_lower for phrase in [
            "сколько работал", "сколько отработал", "статус работы", "рабочий статус"
        ]):
            logs = await self.get_today_logs(user_id)
            work_hours = await self.calculate_work_hours(user_id)
            return self.format_day_summary(logs, work_hours)
        
        return None
