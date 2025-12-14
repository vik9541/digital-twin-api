"""
GitHub Sync - полная синхронизация с GitHub
Автоматически:
- Загружает ТЗ и документацию из GitHub
- Сохраняет отчёты и логи
- Синхронизирует код
"""

import os
import sys
import json
import logging
import httpx
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

# Директории
BOT_DIR = Path(__file__).parent.parent
DOCS_DIR = BOT_DIR / 'docs'
REPORTS_DIR = BOT_DIR / 'reports'
TZ_DIR = BOT_DIR / 'specs'  # Техническое задание


class GitHubSync:
    """Синхронизация с GitHub"""
    
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')  # Personal Access Token
        self.repo_owner = os.getenv('GITHUB_REPO_OWNER', 'vik9541')
        self.repo_name = os.getenv('GITHUB_REPO_NAME', 'digital-twin-api')
        self.specs_repo = os.getenv('GITHUB_SPECS_REPO', 'vik9541/super-brain-digital-twin')
        
        self.base_url = 'https://api.github.com'
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PersonalAssistantBot'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
        
        # Создаём директории
        DOCS_DIR.mkdir(exist_ok=True)
        REPORTS_DIR.mkdir(exist_ok=True)
        TZ_DIR.mkdir(exist_ok=True)
    
    async def fetch_file_from_github(
        self, 
        repo: str, 
        path: str, 
        branch: str = 'main'
    ) -> Optional[str]:
        """Загрузить файл из GitHub"""
        url = f'{self.base_url}/repos/{repo}/contents/{path}?ref={branch}'
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    # Контент в base64
                    import base64
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return content
                else:
                    logger.error(f"GitHub API error: {response.status_code}")
                    return None
            except Exception as e:
                logger.error(f"Error fetching from GitHub: {e}")
                return None
    
    async def sync_specs(self) -> bool:
        """Синхронизировать ТЗ из репозитория документации"""
        logger.info("📥 Синхронизация ТЗ из GitHub...")
        
        # Список файлов ТЗ для загрузки
        spec_files = [
            'COMPLETE_BOT_FIX_SPECIFICATION_DEC14_2025.md',
            'README.md',
        ]
        
        synced = 0
        for filename in spec_files:
            content = await self.fetch_file_from_github(self.specs_repo, filename)
            
            if content:
                local_path = TZ_DIR / filename
                local_path.write_text(content, encoding='utf-8')
                logger.info(f"   ✅ {filename}")
                synced += 1
            else:
                logger.warning(f"   ⚠️ Не удалось загрузить {filename}")
        
        logger.info(f"📥 Синхронизировано ТЗ: {synced}/{len(spec_files)}")
        return synced > 0
    
    async def push_file_to_github(
        self,
        path: str,
        content: str,
        message: str,
        branch: str = 'main'
    ) -> bool:
        """Загрузить файл в GitHub"""
        if not self.token:
            logger.warning("GITHUB_TOKEN не задан, пропускаем push")
            return False
        
        url = f'{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{path}'
        
        import base64
        content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        async with httpx.AsyncClient() as client:
            # Сначала получаем SHA существующего файла (если есть)
            sha = None
            try:
                response = await client.get(url, headers=self.headers)
                if response.status_code == 200:
                    sha = response.json().get('sha')
            except Exception:
                pass
            
            # Создаём/обновляем файл
            data = {
                'message': message,
                'content': content_b64,
                'branch': branch
            }
            if sha:
                data['sha'] = sha
            
            try:
                response = await client.put(url, headers=self.headers, json=data)
                
                if response.status_code in [200, 201]:
                    logger.info(f"✅ Файл загружен: {path}")
                    return True
                else:
                    logger.error(f"❌ Ошибка загрузки: {response.status_code} - {response.text}")
                    return False
            except Exception as e:
                logger.error(f"❌ Ошибка: {e}")
                return False
    
    def save_report(self, report_type: str, content: str, metadata: Dict = None) -> Path:
        """Сохранить отчёт локально"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{report_type}_{timestamp}.md'
        filepath = REPORTS_DIR / filename
        
        # Добавляем метаданные
        header = f"""---
type: {report_type}
date: {datetime.now().isoformat()}
"""
        if metadata:
            for k, v in metadata.items():
                header += f"{k}: {v}\n"
        header += "---\n\n"
        
        filepath.write_text(header + content, encoding='utf-8')
        logger.info(f"📝 Отчёт сохранён: {filepath}")
        
        return filepath
    
    async def sync_reports_to_github(self) -> int:
        """Загрузить все локальные отчёты в GitHub"""
        if not self.token:
            logger.warning("GITHUB_TOKEN не задан")
            return 0
        
        uploaded = 0
        for report_file in REPORTS_DIR.glob('*.md'):
            content = report_file.read_text(encoding='utf-8')
            remote_path = f'bots/personal-assistant-bot/reports/{report_file.name}'
            
            success = await self.push_file_to_github(
                remote_path,
                content,
                f'report: {report_file.stem}'
            )
            if success:
                uploaded += 1
        
        return uploaded
    
    def get_local_spec(self, name: str) -> Optional[str]:
        """Получить локальную копию ТЗ"""
        for ext in ['.md', '.txt', '']:
            path = TZ_DIR / f'{name}{ext}'
            if path.exists():
                return path.read_text(encoding='utf-8')
        return None
    
    def list_specs(self) -> List[str]:
        """Список доступных ТЗ"""
        return [f.stem for f in TZ_DIR.glob('*.md')]
    
    def list_reports(self) -> List[Dict[str, Any]]:
        """Список отчётов"""
        reports = []
        for f in sorted(REPORTS_DIR.glob('*.md'), reverse=True):
            content = f.read_text(encoding='utf-8')
            # Парсим метаданные
            if content.startswith('---'):
                end = content.find('---', 3)
                if end > 0:
                    meta_str = content[3:end].strip()
                    meta = {}
                    for line in meta_str.split('\n'):
                        if ':' in line:
                            k, v = line.split(':', 1)
                            meta[k.strip()] = v.strip()
                    reports.append({
                        'file': f.name,
                        'path': str(f),
                        **meta
                    })
        return reports


# Глобальный экземпляр
_sync: Optional[GitHubSync] = None


def get_github_sync() -> GitHubSync:
    """Получить экземпляр GitHubSync"""
    global _sync
    if _sync is None:
        _sync = GitHubSync()
    return _sync
