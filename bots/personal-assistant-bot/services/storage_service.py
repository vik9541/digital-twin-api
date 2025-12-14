"""
Сервис для работы с Supabase Storage
"""

import os
from typing import Optional
from supabase import create_client, Client


class StorageService:
    """Сервис для загрузки файлов в Supabase Storage"""
    
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if url and key:
            self.client: Client = create_client(url, key)
        else:
            self.client = None
            print("⚠️ Supabase Storage не настроен")
    
    async def upload_file(self, bucket: str, path: str, 
                         file_data: bytes, content_type: str = None) -> Optional[str]:
        """
        Загрузить файл в Storage
        
        Args:
            bucket: Название бакета (projects, receipts, etc.)
            path: Путь внутри бакета (user_id/filename)
            file_data: Содержимое файла в байтах
            content_type: MIME тип файла
        
        Returns:
            URL загруженного файла или None
        """
        if not self.client:
            return None
        
        try:
            # Загрузить файл
            result = self.client.storage.from_(bucket).upload(
                path=path,
                file=file_data,
                file_options={"content-type": content_type} if content_type else None
            )
            
            # Получить публичный URL
            url = self.client.storage.from_(bucket).get_public_url(path)
            
            return url
            
        except Exception as e:
            print(f"❌ Ошибка загрузки файла: {e}")
            return None
    
    async def download_file(self, bucket: str, path: str) -> Optional[bytes]:
        """Скачать файл из Storage"""
        if not self.client:
            return None
        
        try:
            result = self.client.storage.from_(bucket).download(path)
            return result
        except Exception as e:
            print(f"❌ Ошибка скачивания файла: {e}")
            return None
    
    async def delete_file(self, bucket: str, path: str) -> bool:
        """Удалить файл из Storage"""
        if not self.client:
            return False
        
        try:
            self.client.storage.from_(bucket).remove([path])
            return True
        except Exception as e:
            print(f"❌ Ошибка удаления файла: {e}")
            return False
    
    async def list_files(self, bucket: str, folder: str = "") -> list:
        """Получить список файлов в папке"""
        if not self.client:
            return []
        
        try:
            result = self.client.storage.from_(bucket).list(folder)
            return result
        except Exception as e:
            print(f"❌ Ошибка получения списка файлов: {e}")
            return []
    
    async def get_public_url(self, bucket: str, path: str) -> Optional[str]:
        """Получить публичный URL файла"""
        if not self.client:
            return None
        
        try:
            return self.client.storage.from_(bucket).get_public_url(path)
        except Exception as e:
            print(f"❌ Ошибка получения URL: {e}")
            return None
