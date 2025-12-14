"""
Обработчик настроек пользователя
"""

from telegram import Update
from telegram.ext import ContextTypes

from ..services.supabase_service import SupabaseService


class SettingsHandler:
    """Обработчик настроек"""
    
    def __init__(self):
        self.db = SupabaseService()
    
    async def set_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Установить режим работы /mode [режим]"""
        user_id = str(update.effective_user.id)
        
        valid_modes = {
            'executor': {
                'name': 'Исполнитель',
                'description': 'Только выполняю задачи, без советов и лишних слов'
            },
            'advisor': {
                'name': 'Советник',
                'description': 'Даю рекомендации и полезные советы'
            },
            'silent': {
                'name': 'Тихий',
                'description': 'Минимум текста, только результаты'
            },
            'detailed': {
                'name': 'Подробный',
                'description': 'Детальные объяснения всего'
            }
        }
        
        if not context.args:
            # Показать текущий режим и доступные
            prefs = await self.db.get_user_preferences(user_id)
            current = prefs.get('mode', 'executor')
            
            message = f"⚙️ **РЕЖИМЫ РАБОТЫ**\n\n"
            message += f"Текущий режим: **{valid_modes[current]['name']}**\n\n"
            message += "Доступные режимы:\n"
            
            for mode_key, mode_info in valid_modes.items():
                emoji = '✅' if mode_key == current else '⚪'
                message += f"{emoji} `/mode {mode_key}` - {mode_info['name']}\n"
                message += f"   _{mode_info['description']}_\n\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            return
        
        mode = context.args[0].lower()
        
        if mode not in valid_modes:
            await update.message.reply_text(
                f"❌ Неизвестный режим: `{mode}`\n\n"
                f"Доступные: {', '.join(valid_modes.keys())}",
                parse_mode='Markdown'
            )
            return
        
        # Сохранить режим
        await self.db.update_user_preferences(user_id, mode=mode)
        
        mode_info = valid_modes[mode]
        await update.message.reply_text(
            f"✅ Режим **{mode_info['name']}** активирован!\n\n"
            f"_{mode_info['description']}_",
            parse_mode='Markdown'
        )
    
    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать все настройки /settings"""
        user_id = str(update.effective_user.id)
        
        prefs = await self.db.get_user_preferences(user_id)
        
        message = "⚙️ **ТВОИ НАСТРОЙКИ**\n\n"
        
        mode_names = {
            'executor': 'Исполнитель',
            'advisor': 'Советник',
            'silent': 'Тихий',
            'detailed': 'Подробный'
        }
        
        message += f"🎭 Режим: **{mode_names.get(prefs.get('mode', 'executor'), 'executor')}**\n"
        message += f"💡 Советы: {'✅ Включены' if prefs.get('give_advice') else '❌ Выключены'}\n"
        message += f"🌍 Язык: {prefs.get('language', 'ru')}\n"
        message += f"🕐 Часовой пояс: {prefs.get('timezone', 'Europe/Moscow')}\n\n"
        
        message += "**Изменить:**\n"
        message += "• `/mode [режим]` - сменить режим\n"
        message += "• `/advice on/off` - включить/выключить советы\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def toggle_advice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Включить/выключить советы /advice [on/off]"""
        user_id = str(update.effective_user.id)
        
        if not context.args:
            prefs = await self.db.get_user_preferences(user_id)
            current = prefs.get('give_advice', False)
            await update.message.reply_text(
                f"💡 Советы сейчас: {'✅ Включены' if current else '❌ Выключены'}\n\n"
                "Изменить: `/advice on` или `/advice off`",
                parse_mode='Markdown'
            )
            return
        
        value = context.args[0].lower()
        
        if value not in ['on', 'off', 'да', 'нет', '1', '0']:
            await update.message.reply_text("❌ Укажи: `on` или `off`", parse_mode='Markdown')
            return
        
        give_advice = value in ['on', 'да', '1']
        
        await self.db.update_user_preferences(user_id, give_advice=give_advice)
        
        await update.message.reply_text(
            f"✅ Советы {'включены' if give_advice else 'выключены'}!"
        )
