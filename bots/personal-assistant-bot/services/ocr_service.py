"""
Сервис OCR через Google Cloud Vision API
"""

import os
from typing import Optional


class OCRService:
    """Сервис распознавания текста через Google Cloud Vision"""
    
    def __init__(self):
        self.client = None
        
        # Попробовать инициализировать Google Vision
        try:
            from google.cloud import vision
            self.client = vision.ImageAnnotatorClient()
        except Exception as e:
            print(f"⚠️ Google Cloud Vision не настроен: {e}")
    
    async def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """
        Распознать текст с изображения по пути к файлу
        
        Args:
            image_path: Путь к файлу изображения
        
        Returns:
            Распознанный текст или None
        """
        if not self.client:
            return await self._fallback_ocr(image_path)
        
        try:
            from google.cloud import vision
            
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            response = self.client.text_detection(image=image)
            
            texts = response.text_annotations
            
            if texts:
                return texts[0].description
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка OCR: {e}")
            return None
    
    async def extract_text_from_bytes(self, image_bytes: bytes) -> Optional[str]:
        """
        Распознать текст с изображения из байтов
        
        Args:
            image_bytes: Содержимое изображения в байтах
        
        Returns:
            Распознанный текст или None
        """
        if not self.client:
            return await self._fallback_ocr_bytes(image_bytes)
        
        try:
            from google.cloud import vision
            
            image = vision.Image(content=image_bytes)
            response = self.client.text_detection(image=image)
            
            texts = response.text_annotations
            
            if texts:
                return texts[0].description
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка OCR: {e}")
            return None
    
    async def extract_text_from_url(self, image_url: str) -> Optional[str]:
        """
        Распознать текст с изображения по URL
        
        Args:
            image_url: URL изображения
        
        Returns:
            Распознанный текст или None
        """
        if not self.client:
            return None
        
        try:
            from google.cloud import vision
            
            image = vision.Image()
            image.source.image_uri = image_url
            
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            
            if texts:
                return texts[0].description
            
            return None
            
        except Exception as e:
            print(f"❌ Ошибка OCR: {e}")
            return None
    
    async def _fallback_ocr(self, image_path: str) -> Optional[str]:
        """
        Fallback OCR через Tesseract (если Google Vision недоступен)
        """
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='rus+eng')
            
            return text if text.strip() else None
            
        except ImportError:
            print("⚠️ Tesseract не установлен. Установите: pip install pytesseract")
            return None
        except Exception as e:
            print(f"❌ Ошибка Tesseract OCR: {e}")
            return None
    
    async def _fallback_ocr_bytes(self, image_bytes: bytes) -> Optional[str]:
        """
        Fallback OCR через Tesseract для байтов
        """
        try:
            import pytesseract
            from PIL import Image
            import io
            
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image, lang='rus+eng')
            
            return text if text.strip() else None
            
        except ImportError:
            print("⚠️ Tesseract не установлен")
            return None
        except Exception as e:
            print(f"❌ Ошибка Tesseract OCR: {e}")
            return None
