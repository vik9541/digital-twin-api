"""
Первоначальная настройка автосинхронизации с GitHub
Запуск: python scripts/setup_github.py
"""

import os
import sys
import subprocess
from pathlib import Path

BOT_DIR = Path(__file__).parent.parent
ENV_FILE = BOT_DIR / '.env'


def setup_git_credentials():
    """Настройка git для автоматических коммитов"""
    print("🔧 Настройка Git...")
    
    # Проверяем текущую конфигурацию
    result = subprocess.run(['git', 'config', 'user.name'], capture_output=True, text=True)
    if not result.stdout.strip():
        name = input("   Введи имя для git (например: Bot): ") or "PersonalAssistantBot"
        subprocess.run(['git', 'config', 'user.name', name])
    
    result = subprocess.run(['git', 'config', 'user.email'], capture_output=True, text=True)
    if not result.stdout.strip():
        email = input("   Введи email для git: ") or "bot@example.com"
        subprocess.run(['git', 'config', 'user.email', email])
    
    print("   ✅ Git настроен")


def setup_env_variables():
    """Настройка переменных окружения"""
    print("\n🔧 Настройка переменных окружения...")
    
    # Читаем текущий .env
    env_content = ""
    if ENV_FILE.exists():
        env_content = ENV_FILE.read_text()
    
    updates = []
    
    # GitHub Token (для push)
    if 'GITHUB_TOKEN' not in env_content:
        print("\n   Для автоматической загрузки файлов в GitHub нужен Personal Access Token.")
        print("   Создай его на: https://github.com/settings/tokens/new")
        print("   Права: repo (full control)")
        token = input("   Введи GITHUB_TOKEN (или Enter чтобы пропустить): ").strip()
        if token:
            updates.append(f'GITHUB_TOKEN={token}')
    
    # GitHub repo info
    if 'GITHUB_REPO_OWNER' not in env_content:
        owner = input("   GitHub username (vik9541): ").strip() or 'vik9541'
        updates.append(f'GITHUB_REPO_OWNER={owner}')
    
    if 'GITHUB_REPO_NAME' not in env_content:
        repo = input("   Имя репозитория (digital-twin-api): ").strip() or 'digital-twin-api'
        updates.append(f'GITHUB_REPO_NAME={repo}')
    
    if 'GITHUB_SPECS_REPO' not in env_content:
        specs = input("   Репозиторий с ТЗ (vik9541/super-brain-digital-twin): ").strip() or 'vik9541/super-brain-digital-twin'
        updates.append(f'GITHUB_SPECS_REPO={specs}')
    
    # Добавляем в .env
    if updates:
        with open(ENV_FILE, 'a') as f:
            f.write('\n# GitHub Sync\n')
            for line in updates:
                f.write(line + '\n')
        print(f"   ✅ Добавлено {len(updates)} переменных в .env")
    else:
        print("   ✅ Все переменные уже настроены")


def create_directories():
    """Создание необходимых директорий"""
    print("\n🔧 Создание директорий...")
    
    dirs = [
        BOT_DIR / 'docs',
        BOT_DIR / 'reports',
        BOT_DIR / 'specs',
    ]
    
    for d in dirs:
        d.mkdir(exist_ok=True)
        # Создаём .gitkeep чтобы директория попала в git
        (d / '.gitkeep').touch()
        print(f"   ✅ {d.name}/")


def test_sync():
    """Тест синхронизации"""
    print("\n🧪 Тестирование синхронизации...")
    
    # Загружаем переменные окружения
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
    
    sys.path.insert(0, str(BOT_DIR))
    
    import asyncio
    from services.github_sync import get_github_sync
    
    async def test():
        sync = get_github_sync()
        
        # Тест загрузки ТЗ
        print("   📥 Загрузка ТЗ из GitHub...")
        success = await sync.sync_specs()
        if success:
            print("   ✅ ТЗ загружено")
            specs = sync.list_specs()
            for s in specs:
                print(f"      • {s}")
        else:
            print("   ⚠️ Не удалось загрузить ТЗ")
    
    asyncio.run(test())


def main():
    print("🚀 Настройка автосинхронизации с GitHub")
    print("=" * 50)
    
    setup_git_credentials()
    setup_env_variables()
    create_directories()
    
    # Спрашиваем про тест
    if input("\n🧪 Протестировать синхронизацию? (y/n): ").lower() == 'y':
        test_sync()
    
    print("\n" + "=" * 50)
    print("✅ Настройка завершена!")
    print("\nТеперь бот будет:")
    print("• Загружать ТЗ из GitHub при старте")
    print("• Синхронизировать отчёты каждый час")
    print("• Автоматически коммитить изменения")
    print("\nЗапусти бота: python main.py")


if __name__ == '__main__':
    main()
