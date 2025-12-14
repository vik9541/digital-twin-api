"""
Сервис для работы с Supabase БД
"""

import os
from datetime import datetime, timedelta
from utils.timezone import now_naive as moscow_now
from typing import Optional, List, Dict, Any
from supabase import create_client, Client


class SupabaseService:
    """Сервис для работы с Supabase"""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if url and key:
            self.client: Client = create_client(url, key)
        else:
            self.client = None
            print("⚠️ Supabase не настроен (SUPABASE_URL, SUPABASE_KEY)")
    
    # ==========================================
    # ПОЛЬЗОВАТЕЛИ
    # ==========================================
    
    async def ensure_user_exists(self, user_id: str) -> Dict:
        """Создать пользователя если не существует"""
        if not self.client:
            return {}
        
        # Проверить существование
        result = self.client.table('user_preferences').select('*').eq('user_id', user_id).execute()
        
        if result.data:
            return result.data[0]
        
        # Создать нового
        new_user = {
            'user_id': user_id,
            'mode': 'executor',
            'give_advice': False,
            'language': 'ru',
            'timezone': 'Europe/Moscow'
        }
        
        result = self.client.table('user_preferences').insert(new_user).execute()
        return result.data[0] if result.data else {}
    
    async def get_user_preferences(self, user_id: str) -> Dict:
        """Получить настройки пользователя"""
        if not self.client:
            return {'mode': 'executor', 'give_advice': False}
        
        result = self.client.table('user_preferences').select('*').eq('user_id', user_id).execute()
        
        if result.data:
            return result.data[0]
        
        # Создать если нет
        return await self.ensure_user_exists(user_id)
    
    async def update_user_preferences(self, user_id: str, **kwargs) -> bool:
        """Обновить настройки пользователя"""
        if not self.client:
            return False
        
        await self.ensure_user_exists(user_id)
        
        result = self.client.table('user_preferences').update(kwargs).eq('user_id', user_id).execute()
        return bool(result.data)
    
    async def get_user_stats(self, user_id: str) -> Dict:
        """Получить статистику пользователя"""
        if not self.client:
            return {}
        
        stats = {}
        
        # Проекты
        projects = self.client.table('user_projects').select('status').eq('user_id', user_id).execute()
        stats['projects_count'] = len(projects.data) if projects.data else 0
        stats['active_projects'] = sum(1 for p in (projects.data or []) if p['status'] == 'active')
        
        # Задачи
        tasks = self.client.table('user_tasks').select('status').eq('user_id', user_id).execute()
        stats['tasks_count'] = len(tasks.data) if tasks.data else 0
        stats['pending_tasks'] = sum(1 for t in (tasks.data or []) if t['status'] == 'pending')
        
        # Чеки
        receipts = self.client.table('receipts').select('id').eq('user_id', user_id).execute()
        stats['receipts_count'] = len(receipts.data) if receipts.data else 0
        
        # Здоровье
        health = self.client.table('health_diary').select('id').eq('user_id', user_id).execute()
        stats['health_entries'] = len(health.data) if health.data else 0
        
        return stats
    
    # ==========================================
    # ПРОЕКТЫ
    # ==========================================
    
    async def get_user_projects(self, user_id: str, status: str = None) -> List[Dict]:
        """Получить проекты пользователя"""
        if not self.client:
            return []
        
        query = self.client.table('user_projects').select('*').eq('user_id', user_id)
        
        if status:
            query = query.eq('status', status)
        
        result = query.order('created_at', desc=True).execute()
        
        projects = result.data or []
        
        # Добавить счетчики файлов и задач
        for project in projects:
            files = self.client.table('project_files').select('id').eq('project_id', project['id']).execute()
            project['files_count'] = len(files.data) if files.data else 0
            
            tasks = self.client.table('user_tasks').select('id').eq('project_id', project['id']).execute()
            project['tasks_count'] = len(tasks.data) if tasks.data else 0
        
        return projects
    
    async def count_user_projects(self, user_id: str) -> int:
        """Количество проектов пользователя"""
        if not self.client:
            return 0
        
        result = self.client.table('user_projects').select('id').eq('user_id', user_id).execute()
        return len(result.data) if result.data else 0
    
    async def create_project(self, user_id: str, project_name: str, description: str = None) -> Dict:
        """Создать проект"""
        if not self.client:
            return {}
        
        project = {
            'user_id': user_id,
            'project_name': project_name,
            'description': description,
            'status': 'active'
        }
        
        result = self.client.table('user_projects').insert(project).execute()
        return result.data[0] if result.data else {}
    
    async def get_project_by_id(self, project_id: str, user_id: str) -> Optional[Dict]:
        """Получить проект по ID"""
        if not self.client:
            return None
        
        # Поиск по началу UUID
        result = self.client.table('user_projects').select('*').eq('user_id', user_id).execute()
        
        for project in (result.data or []):
            if project['id'].startswith(project_id):
                return project
        
        return None
    
    async def update_project_status(self, project_id: str, user_id: str, status: str) -> bool:
        """Обновить статус проекта"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return False
        
        result = self.client.table('user_projects').update({'status': status}).eq('id', project['id']).execute()
        return bool(result.data)
    
    async def delete_project(self, project_id: str, user_id: str) -> bool:
        """Удалить проект"""
        project = await self.get_project_by_id(project_id, user_id)
        if not project:
            return False
        
        result = self.client.table('user_projects').delete().eq('id', project['id']).execute()
        return bool(result.data)
    
    async def get_project_files(self, project_id: str) -> List[Dict]:
        """Получить файлы проекта"""
        if not self.client:
            return []
        
        result = self.client.table('project_files').select('*').eq('project_id', project_id).execute()
        return result.data or []
    
    async def get_project_tasks(self, project_id: str) -> List[Dict]:
        """Получить задачи проекта"""
        if not self.client:
            return []
        
        result = self.client.table('user_tasks').select('*').eq('project_id', project_id).execute()
        return result.data or []
    
    async def save_project_file(self, project_id: Optional[str], file_name: str, 
                                file_url: str, file_size: int, file_type: str,
                                user_id: str = None) -> Dict:
        """Сохранить информацию о файле"""
        if not self.client:
            return {}
        
        file_data = {
            'project_id': project_id,
            'file_name': file_name,
            'file_url': file_url,
            'file_size': file_size,
            'file_type': file_type
        }
        
        result = self.client.table('project_files').insert(file_data).execute()
        return result.data[0] if result.data else {}
    
    # ==========================================
    # ЗАДАЧИ
    # ==========================================
    
    async def get_user_tasks(self, user_id: str, status: str = None) -> List[Dict]:
        """Получить задачи пользователя"""
        if not self.client:
            return []
        
        query = self.client.table('user_tasks').select('*').eq('user_id', user_id)
        
        if status:
            query = query.eq('status', status)
        
        result = query.order('created_at', desc=True).execute()
        return result.data or []
    
    async def count_user_tasks(self, user_id: str) -> int:
        """Количество задач пользователя"""
        if not self.client:
            return 0
        
        result = self.client.table('user_tasks').select('id').eq('user_id', user_id).execute()
        return len(result.data) if result.data else 0
    
    async def create_task(self, user_id: str, task_description: str, 
                         priority: str = 'medium', project_id: str = None) -> Dict:
        """Создать задачу"""
        if not self.client:
            return {}
        
        task = {
            'user_id': user_id,
            'task_description': task_description,
            'priority': priority,
            'project_id': project_id,
            'status': 'pending'
        }
        
        result = self.client.table('user_tasks').insert(task).execute()
        return result.data[0] if result.data else {}
    
    async def update_task_status(self, task_id: str, status: str) -> bool:
        """Обновить статус задачи"""
        if not self.client:
            return False
        
        result = self.client.table('user_tasks').update({'status': status}).eq('id', task_id).execute()
        return bool(result.data)
    
    async def update_task_priority(self, task_id: str, priority: str) -> bool:
        """Обновить приоритет задачи"""
        if not self.client:
            return False
        
        result = self.client.table('user_tasks').update({'priority': priority}).eq('id', task_id).execute()
        return bool(result.data)
    
    # ==========================================
    # ЧЕКИ
    # ==========================================
    
    async def save_receipt(self, user_id: str, store_name: str = None,
                          receipt_date: str = None, total_sum: float = None,
                          items: List[Dict] = None, raw_text: str = None) -> Dict:
        """Сохранить чек"""
        if not self.client:
            return {}
        
        receipt_data = {
            'user_id': user_id,
            'store_name': store_name,
            'receipt_date': receipt_date,
            'total_sum': total_sum,
            'metadata': {'raw_text': raw_text}
        }
        
        result = self.client.table('receipts').insert(receipt_data).execute()
        
        if not result.data:
            return {}
        
        receipt = result.data[0]
        
        # Сохранить товары
        if items:
            for item in items:
                item_data = {
                    'receipt_id': receipt['id'],
                    'item_name': item.get('name'),
                    'category': item.get('category'),
                    'price': item.get('price'),
                    'quantity': item.get('quantity', 1)
                }
                self.client.table('receipt_items').insert(item_data).execute()
        
        return receipt
    
    async def get_user_receipts(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Получить чеки пользователя"""
        if not self.client:
            return []
        
        result = self.client.table('receipts').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
        return result.data or []
    
    async def get_receipt_stats(self, user_id: str) -> Dict:
        """Статистика по чекам"""
        if not self.client:
            return {}
        
        receipts = self.client.table('receipts').select('*').eq('user_id', user_id).execute()
        
        if not receipts.data:
            return {}
        
        total_spent = sum(r.get('total_sum', 0) or 0 for r in receipts.data)
        
        # Получить все товары
        receipt_ids = [r['id'] for r in receipts.data]
        items = []
        for rid in receipt_ids:
            result = self.client.table('receipt_items').select('*').eq('receipt_id', rid).execute()
            items.extend(result.data or [])
        
        # По категориям
        by_category = {}
        for item in items:
            cat = item.get('category', 'Прочее')
            by_category[cat] = by_category.get(cat, 0) + (item.get('price', 0) or 0)
        
        # По магазинам
        by_store = {}
        for r in receipts.data:
            store = r.get('store_name', 'Неизвестно')
            by_store[store] = by_store.get(store, 0) + (r.get('total_sum', 0) or 0)
        
        return {
            'total_spent': total_spent,
            'receipts_count': len(receipts.data),
            'items_count': len(items),
            'by_category': by_category,
            'by_store': by_store
        }
    
    # ==========================================
    # ЗДОРОВЬЕ
    # ==========================================
    
    async def save_health_entry(self, user_id: str, entry_type: str,
                               description: str, data: Dict = None) -> Dict:
        """Сохранить запись в дневник здоровья"""
        if not self.client:
            return {}
        
        entry = {
            'user_id': user_id,
            'entry_type': entry_type,
            'description': description,
            'data': data or {}
        }
        
        result = self.client.table('health_diary').insert(entry).execute()
        return result.data[0] if result.data else {}
    
    async def get_health_entries(self, user_id: str, days: int = 1) -> List[Dict]:
        """Получить записи за N дней"""
        if not self.client:
            return []
        
        since_date = (moscow_now() - timedelta(days=days)).isoformat()
        
        result = self.client.table('health_diary').select('*').eq('user_id', user_id).gte('created_at', since_date).order('created_at', desc=True).execute()
        
        return result.data or []
