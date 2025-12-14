"""
Обработчик анализа чеков
"""

from telegram import Update
from telegram.ext import ContextTypes
from typing import Dict

from ..services.supabase_service import SupabaseService
from ..services.ocr_service import OCRService
from ..services.receipt_parser import ReceiptParser
from ..services.market_service import MarketService


class ReceiptsHandler:
    """Обработчик чеков"""
    
    def __init__(self):
        self.db = SupabaseService()
        self.ocr = OCRService()
        self.parser = ReceiptParser()
        self.market = MarketService()
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка фото чека"""
        user_id = str(update.effective_user.id)
        
        if not update.message.photo:
            return
        
        # Отправить сообщение о обработке
        processing_msg = await update.message.reply_text("⏳ Анализирую чек...")
        
        try:
            # Скачать фото (лучшее качество)
            photo = update.message.photo[-1]
            file = await photo.get_file()
            file_bytes = await file.download_as_bytearray()
            
            # Распознать текст (OCR)
            text = await self.ocr.extract_text_from_bytes(bytes(file_bytes))
            
            if not text:
                await processing_msg.edit_text(
                    "❌ Не удалось распознать текст.\n"
                    "Попробуй сделать более четкое фото."
                )
                return
            
            # Парсить структуру чека
            parsed = await self.parser.parse_receipt_text(text)
            
            # Сохранить в БД
            receipt = await self.db.save_receipt(
                user_id=user_id,
                store_name=parsed.get('store_name'),
                receipt_date=parsed.get('receipt_date'),
                total_sum=parsed.get('total_sum'),
                items=parsed.get('items', []),
                raw_text=text
            )
            
            # Форматировать результат
            message = self._format_receipt_analysis(parsed)
            
            # Добавить сравнение цен (если есть товары)
            if parsed.get('items'):
                cheaper = await self.market.find_cheaper_items(parsed['items'][:5])
                if cheaper:
                    message += "\n\n💡 **МОЖНО ДЕШЕВЛЕ:**\n"
                    for item in cheaper:
                        savings = item['original_price'] - item['cheaper_price']
                        message += f"• {item['item_name']}: {item['cheaper_price']}₽ в {item['store']} (экономия {savings:.0f}₽)\n"
            
            await processing_msg.edit_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await processing_msg.edit_text(f"❌ Ошибка: {str(e)}")
    
    def _format_receipt_analysis(self, parsed: Dict) -> str:
        """Форматировать результат анализа"""
        message = "✅ **ЧЕК ПРОАНАЛИЗИРОВАН**\n\n"
        
        store = parsed.get('store_name', 'Неизвестный магазин')
        message += f"🏪 **{store}**\n"
        
        if parsed.get('receipt_date'):
            message += f"📅 {parsed['receipt_date']}"
            if parsed.get('receipt_time'):
                message += f" {parsed['receipt_time']}"
            message += "\n"
        
        if parsed.get('address'):
            message += f"📍 {parsed['address']}\n"
        
        message += "\n🛒 **ТОВАРЫ:**\n"
        
        items = parsed.get('items', [])
        if items:
            # Группировать по категориям
            by_category = {}
            for item in items:
                cat = item.get('category', 'Прочее')
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(item)
            
            for category, cat_items in by_category.items():
                cat_total = sum(i.get('price', 0) for i in cat_items)
                message += f"\n**{category}** ({cat_total:.0f}₽):\n"
                for item in cat_items:
                    message += f"• {item['name']} - {item.get('price', 0):.0f}₽\n"
        else:
            message += "_Товары не распознаны_\n"
        
        total = parsed.get('total_sum', 0)
        message += f"\n💰 **ИТОГО: {total:.0f}₽**"
        
        return message
    
    async def receipt_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """История покупок /receipt history"""
        user_id = str(update.effective_user.id)
        
        receipts = await self.db.get_user_receipts(user_id, limit=10)
        
        if not receipts:
            await update.message.reply_text(
                "🧾 История покупок пуста.\n\n"
                "Отправь фото чека для анализа!"
            )
            return
        
        message = "🧾 **ПОСЛЕДНИЕ ПОКУПКИ:**\n\n"
        
        for receipt in receipts:
            store = receipt.get('store_name', 'Магазин')
            date = receipt.get('receipt_date', receipt['created_at'])[:10]
            total = receipt.get('total_sum', 0)
            
            message += f"• {date} - **{store}** - {total:.0f}₽\n"
        
        # Статистика
        total_spent = sum(r.get('total_sum', 0) for r in receipts)
        message += f"\n📊 Всего за период: **{total_spent:.0f}₽**"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def receipt_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статистика расходов /receipt stats"""
        user_id = str(update.effective_user.id)
        
        stats = await self.db.get_receipt_stats(user_id)
        
        if not stats:
            await update.message.reply_text("📊 Недостаточно данных для статистики")
            return
        
        message = "📊 **СТАТИСТИКА РАСХОДОВ**\n\n"
        
        message += f"💰 Всего потрачено: **{stats.get('total_spent', 0):.0f}₽**\n"
        message += f"🧾 Чеков: {stats.get('receipts_count', 0)}\n"
        message += f"📦 Товаров: {stats.get('items_count', 0)}\n\n"
        
        if stats.get('by_category'):
            message += "**По категориям:**\n"
            for cat, amount in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
                message += f"• {cat}: {amount:.0f}₽\n"
        
        if stats.get('by_store'):
            message += "\n**По магазинам:**\n"
            for store, amount in sorted(stats['by_store'].items(), key=lambda x: -x[1])[:5]:
                message += f"• {store}: {amount:.0f}₽\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
