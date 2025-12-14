"""
Сервис экспорта данных
Поддержка CSV, JSON, Excel
"""

import csv
import json
import io
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import logging
from utils.timezone import now_naive as moscow_now

logger = logging.getLogger(__name__)


class ExportService:
    """Сервис экспорта данных"""
    
    @staticmethod
    def export_tasks_csv(tasks: List[Dict]) -> bytes:
        """Экспорт задач в CSV"""
        output = io.StringIO()
        
        fieldnames = ['Задача', 'Статус', 'Приоритет', 'Проект', 'Дата создания', 'Дедлайн']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        status_map = {'pending': 'В работе', 'done': 'Выполнено', 'in_progress': 'В процессе'}
        priority_map = {'low': 'Низкий', 'medium': 'Средний', 'high': 'Высокий'}
        
        for task in tasks:
            writer.writerow({
                'Задача': task.get('task_description', ''),
                'Статус': status_map.get(task.get('status', ''), task.get('status', '')),
                'Приоритет': priority_map.get(task.get('priority', ''), task.get('priority', '')),
                'Проект': task.get('project_name', ''),
                'Дата создания': task.get('created_at', '')[:10] if task.get('created_at') else '',
                'Дедлайн': task.get('due_date', '')[:10] if task.get('due_date') else ''
            })
        
        return output.getvalue().encode('utf-8-sig')  # UTF-8 BOM для Excel
    
    @staticmethod
    def export_tasks_json(tasks: List[Dict]) -> bytes:
        """Экспорт задач в JSON"""
        export_data = {
            'exported_at': moscow_now().isoformat(),
            'count': len(tasks),
            'tasks': tasks
        }
        return json.dumps(export_data, ensure_ascii=False, indent=2).encode('utf-8')
    
    @staticmethod
    def export_projects_csv(projects: List[Dict]) -> bytes:
        """Экспорт проектов в CSV"""
        output = io.StringIO()
        
        fieldnames = ['Название', 'Описание', 'Статус', 'Дата создания', 'Дедлайн']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        status_map = {'active': 'Активен', 'done': 'Завершен', 'archived': 'Архив'}
        
        for project in projects:
            writer.writerow({
                'Название': project.get('project_name', ''),
                'Описание': project.get('description', ''),
                'Статус': status_map.get(project.get('status', ''), project.get('status', '')),
                'Дата создания': project.get('created_at', '')[:10] if project.get('created_at') else '',
                'Дедлайн': project.get('deadline', '')[:10] if project.get('deadline') else ''
            })
        
        return output.getvalue().encode('utf-8-sig')
    
    @staticmethod
    def export_receipts_csv(receipts: List[Dict]) -> bytes:
        """Экспорт чеков в CSV"""
        output = io.StringIO()
        
        fieldnames = ['Дата', 'Магазин', 'Адрес', 'Сумма', 'Товаров']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for receipt in receipts:
            writer.writerow({
                'Дата': receipt.get('receipt_date', receipt.get('created_at', ''))[:10],
                'Магазин': receipt.get('store_name', ''),
                'Адрес': receipt.get('store_location', ''),
                'Сумма': receipt.get('total_sum', 0),
                'Товаров': len(receipt.get('items', []))
            })
        
        return output.getvalue().encode('utf-8-sig')
    
    @staticmethod
    def export_receipt_items_csv(receipts: List[Dict]) -> bytes:
        """Экспорт товаров из чеков в CSV"""
        output = io.StringIO()
        
        fieldnames = ['Дата', 'Магазин', 'Товар', 'Категория', 'Цена', 'Количество']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for receipt in receipts:
            receipt_date = receipt.get('receipt_date', receipt.get('created_at', ''))[:10]
            store = receipt.get('store_name', '')
            
            for item in receipt.get('items', []):
                writer.writerow({
                    'Дата': receipt_date,
                    'Магазин': store,
                    'Товар': item.get('item_name', ''),
                    'Категория': item.get('category', ''),
                    'Цена': item.get('price', 0),
                    'Количество': item.get('quantity', 1)
                })
        
        return output.getvalue().encode('utf-8-sig')
    
    @staticmethod
    def export_health_csv(entries: List[Dict]) -> bytes:
        """Экспорт дневника здоровья в CSV"""
        output = io.StringIO()
        
        fieldnames = ['Дата', 'Время', 'Тип', 'Описание']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        type_map = {
            'food': 'Питание',
            'activity': 'Активность',
            'sleep': 'Сон',
            'habit': 'Привычка',
            'mood': 'Настроение',
            'measurement': 'Измерение',
            'note': 'Заметка'
        }
        
        for entry in entries:
            writer.writerow({
                'Дата': entry.get('entry_date', ''),
                'Время': entry.get('entry_time', ''),
                'Тип': type_map.get(entry.get('entry_type', ''), entry.get('entry_type', '')),
                'Описание': entry.get('description', '')
            })
        
        return output.getvalue().encode('utf-8-sig')
    
    @staticmethod
    def export_full_backup(data: Dict) -> bytes:
        """Полный экспорт всех данных в JSON"""
        export_data = {
            'exported_at': moscow_now().isoformat(),
            'version': '1.0',
            'data': data
        }
        return json.dumps(export_data, ensure_ascii=False, indent=2, default=str).encode('utf-8')
    
    @staticmethod
    def generate_expense_report(receipts: List[Dict]) -> Dict:
        """Генерация отчета о расходах"""
        if not receipts:
            return {'total': 0, 'count': 0, 'by_store': {}, 'by_category': {}}
        
        total = sum(r.get('total_sum', 0) for r in receipts)
        
        # По магазинам
        by_store = {}
        for r in receipts:
            store = r.get('store_name', 'Неизвестно')
            by_store[store] = by_store.get(store, 0) + r.get('total_sum', 0)
        
        # По категориям
        by_category = {}
        for r in receipts:
            for item in r.get('items', []):
                cat = item.get('category', 'Прочее')
                by_category[cat] = by_category.get(cat, 0) + item.get('price', 0)
        
        # Сортировка
        by_store = dict(sorted(by_store.items(), key=lambda x: x[1], reverse=True))
        by_category = dict(sorted(by_category.items(), key=lambda x: x[1], reverse=True))
        
        return {
            'total': total,
            'count': len(receipts),
            'average': total / len(receipts) if receipts else 0,
            'by_store': by_store,
            'by_category': by_category
        }
    
    @staticmethod
    def format_expense_report(report: Dict) -> str:
        """Форматирование отчета о расходах для отображения"""
        lines = ["📊 **ОТЧЕТ О РАСХОДАХ**\n"]
        
        lines.append(f"💰 **Всего:** {report['total']:.0f}₽")
        lines.append(f"🧾 **Чеков:** {report['count']}")
        lines.append(f"📈 **Средний чек:** {report['average']:.0f}₽\n")
        
        # Топ магазинов
        if report['by_store']:
            lines.append("🏪 **По магазинам:**")
            for store, amount in list(report['by_store'].items())[:5]:
                lines.append(f"  • {store}: {amount:.0f}₽")
        
        # Топ категорий
        if report['by_category']:
            lines.append("\n📦 **По категориям:**")
            for cat, amount in list(report['by_category'].items())[:5]:
                lines.append(f"  • {cat}: {amount:.0f}₽")
        
        return "\n".join(lines)
