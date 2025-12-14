"""
Обработчик экспорта данных
"""

import logging
from datetime import datetime, date, timedelta
from telegram import Update
from telegram.ext import ContextTypes

from services.supabase_service import SupabaseService
from services.export_service import ExportService
from services.expense_analytics import ExpenseAnalytics

logger = logging.getLogger(__name__)


class ExportHandler:
    """Обработчик команд экспорта"""
    
    def __init__(self):
        self.db = SupabaseService()
        self.export = ExportService()
        self.analytics = ExpenseAnalytics(self.db)
    
    async def export_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Экспорт данных
        /export tasks - экспорт задач в CSV
        /export projects - экспорт проектов
        /export receipts - экспорт чеков
        /export health - экспорт дневника здоровья
        /export all - полный бэкап в JSON
        """
        if not context.args:
            await update.message.reply_text(
                "📤 **ЭКСПОРТ ДАННЫХ**\n\n"
                "Команды:\n"
                "• `/export tasks` - задачи (CSV)\n"
                "• `/export projects` - проекты (CSV)\n"
                "• `/export receipts` - чеки (CSV)\n"
                "• `/export items` - товары из чеков (CSV)\n"
                "• `/export health` - дневник здоровья (CSV)\n"
                "• `/export all` - полный бэкап (JSON)",
                parse_mode='Markdown'
            )
            return
        
        user_id = str(update.effective_user.id)
        export_type = context.args[0].lower()
        
        await update.message.reply_text("⏳ Готовлю экспорт...")
        
        try:
            if export_type == 'tasks':
                await self._export_tasks(update, user_id)
            elif export_type == 'projects':
                await self._export_projects(update, user_id)
            elif export_type == 'receipts':
                await self._export_receipts(update, user_id)
            elif export_type == 'items':
                await self._export_items(update, user_id)
            elif export_type == 'health':
                await self._export_health(update, user_id)
            elif export_type == 'all':
                await self._export_all(update, user_id)
            else:
                await update.message.reply_text(f"❌ Неизвестный тип экспорта: {export_type}")
        
        except Exception as e:
            logger.error(f"Export error: {e}")
            await update.message.reply_text(f"❌ Ошибка экспорта: {str(e)}")
    
    async def _export_tasks(self, update: Update, user_id: str):
        """Экспорт задач"""
        tasks = await self.db.get_user_tasks(user_id, status=None)
        
        if not tasks:
            await update.message.reply_text("📭 Нет задач для экспорта")
            return
        
        csv_data = self.export.export_tasks_csv(tasks)
        
        from io import BytesIO
        file = BytesIO(csv_data)
        file.name = f"tasks_{date.today()}.csv"
        
        await update.message.reply_document(
            document=file,
            filename=file.name,
            caption=f"📋 Экспорт задач ({len(tasks)} шт.)"
        )
    
    async def _export_projects(self, update: Update, user_id: str):
        """Экспорт проектов"""
        projects = await self.db.get_user_projects(user_id)
        
        if not projects:
            await update.message.reply_text("📭 Нет проектов для экспорта")
            return
        
        csv_data = self.export.export_projects_csv(projects)
        
        from io import BytesIO
        file = BytesIO(csv_data)
        file.name = f"projects_{date.today()}.csv"
        
        await update.message.reply_document(
            document=file,
            filename=file.name,
            caption=f"📂 Экспорт проектов ({len(projects)} шт.)"
        )
    
    async def _export_receipts(self, update: Update, user_id: str):
        """Экспорт чеков"""
        receipts = await self.db.get_user_receipts(user_id, limit=500)
        
        if not receipts:
            await update.message.reply_text("📭 Нет чеков для экспорта")
            return
        
        csv_data = self.export.export_receipts_csv(receipts)
        
        from io import BytesIO
        file = BytesIO(csv_data)
        file.name = f"receipts_{date.today()}.csv"
        
        await update.message.reply_document(
            document=file,
            filename=file.name,
            caption=f"🧾 Экспорт чеков ({len(receipts)} шт.)"
        )
    
    async def _export_items(self, update: Update, user_id: str):
        """Экспорт товаров из чеков"""
        receipts = await self.db.get_user_receipts(user_id, limit=500)
        
        if not receipts:
            await update.message.reply_text("📭 Нет данных для экспорта")
            return
        
        # Загрузить товары для каждого чека
        for r in receipts:
            items = await self.db.get_receipt_items(r['id'])
            r['items'] = items
        
        csv_data = self.export.export_receipt_items_csv(receipts)
        
        from io import BytesIO
        file = BytesIO(csv_data)
        file.name = f"receipt_items_{date.today()}.csv"
        
        total_items = sum(len(r.get('items', [])) for r in receipts)
        
        await update.message.reply_document(
            document=file,
            filename=file.name,
            caption=f"🛒 Экспорт товаров ({total_items} позиций)"
        )
    
    async def _export_health(self, update: Update, user_id: str):
        """Экспорт дневника здоровья"""
        entries = await self.db.get_health_entries(user_id, days=365)
        
        if not entries:
            await update.message.reply_text("📭 Нет записей для экспорта")
            return
        
        csv_data = self.export.export_health_csv(entries)
        
        from io import BytesIO
        file = BytesIO(csv_data)
        file.name = f"health_diary_{date.today()}.csv"
        
        await update.message.reply_document(
            document=file,
            filename=file.name,
            caption=f"💪 Экспорт дневника здоровья ({len(entries)} записей)"
        )
    
    async def _export_all(self, update: Update, user_id: str):
        """Полный экспорт всех данных"""
        # Сбор всех данных
        data = {
            'tasks': await self.db.get_user_tasks(user_id, status=None),
            'projects': await self.db.get_user_projects(user_id),
            'receipts': await self.db.get_user_receipts(user_id, limit=1000),
            'health_entries': await self.db.get_health_entries(user_id, days=365),
            'preferences': await self.db.get_user_preferences(user_id)
        }
        
        # Загрузить товары для чеков
        for r in data['receipts']:
            items = await self.db.get_receipt_items(r['id'])
            r['items'] = items
        
        json_data = self.export.export_full_backup(data)
        
        from io import BytesIO
        file = BytesIO(json_data)
        file.name = f"backup_{user_id}_{date.today()}.json"
        
        await update.message.reply_document(
            document=file,
            filename=file.name,
            caption="📦 Полный бэкап данных"
        )
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Отчеты
        /report month - отчет за месяц
        /report week - отчет за неделю
        /report top - топ расходов
        /report tips - советы по экономии
        """
        if not context.args:
            await update.message.reply_text(
                "📊 **ОТЧЕТЫ**\n\n"
                "• `/report month` - расходы за месяц\n"
                "• `/report week` - расходы за неделю\n"
                "• `/report top` - топ-10 покупок\n"
                "• `/report tips` - советы по экономии",
                parse_mode='Markdown'
            )
            return
        
        user_id = str(update.effective_user.id)
        report_type = context.args[0].lower()
        
        try:
            if report_type == 'month':
                stats = await self.analytics.get_monthly_stats(user_id)
                report = self.analytics.format_monthly_report(stats)
                await update.message.reply_text(report, parse_mode='Markdown')
            
            elif report_type == 'week':
                # Сравнение этой и прошлой недели
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                last_week_start = week_start - timedelta(days=7)
                
                comparison = await self.analytics.compare_periods(
                    user_id,
                    (last_week_start, week_start - timedelta(days=1)),
                    (week_start, today)
                )
                
                trend_emoji = {'up': '📈', 'down': '📉', 'stable': '➡️'}.get(comparison['trend'], '')
                
                await update.message.reply_text(
                    f"📊 **СРАВНЕНИЕ НЕДЕЛЬ**\n\n"
                    f"**Прошлая неделя:**\n"
                    f"  💰 {comparison['period1']['total']:.0f}₽ ({comparison['period1']['count']} чеков)\n\n"
                    f"**Эта неделя:**\n"
                    f"  💰 {comparison['period2']['total']:.0f}₽ ({comparison['period2']['count']} чеков)\n\n"
                    f"{trend_emoji} **Разница:** {comparison['difference']:+.0f}₽ ({comparison['difference_percent']:+.0f}%)",
                    parse_mode='Markdown'
                )
            
            elif report_type == 'top':
                top_items = await self.analytics.get_top_expenses(user_id, days=30)
                
                if not top_items:
                    await update.message.reply_text("📭 Нет данных о покупках")
                    return
                
                lines = ["🏆 **ТОП-10 ПОКУПОК ЗА МЕСЯЦ:**\n"]
                for i, item in enumerate(top_items[:10], 1):
                    lines.append(f"{i}. **{item['price']:.0f}₽** - {item['name'][:30]}")
                    lines.append(f"   _{item['store']}_ | {item['date']}")
                
                await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
            
            elif report_type == 'tips':
                tips = await self.analytics.get_savings_recommendations(user_id)
                
                lines = ["💡 **СОВЕТЫ ПО ЭКОНОМИИ:**\n"]
                for tip in tips:
                    lines.append(f"• {tip}")
                
                await update.message.reply_text('\n'.join(lines), parse_mode='Markdown')
            
            else:
                await update.message.reply_text(f"❌ Неизвестный тип отчета: {report_type}")
        
        except Exception as e:
            logger.error(f"Report error: {e}")
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
