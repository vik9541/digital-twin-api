"""
Скрипт быстрого деплоя: проверки + коммит + push
Запуск: python scripts/deploy.py "Сообщение коммита"
"""

import os
import sys
import subprocess
from pathlib import Path

BOT_DIR = Path(__file__).parent.parent


def run_cmd(cmd: str, cwd: Path = BOT_DIR) -> tuple[int, str]:
    """Выполнить команду и вернуть код выхода и вывод"""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    output = result.stdout + result.stderr
    return result.returncode, output


def main():
    print("🚀 Деплой Personal Assistant Bot")
    print("=" * 50)
    
    # 1. Проверка синтаксиса Python
    print("\n📋 1/5 Проверка синтаксиса...")
    files_to_check = [
        'main.py',
        'config.py',
        'handlers/*.py',
        'services/*.py',
        'models/*.py',
    ]
    
    for pattern in files_to_check:
        for f in BOT_DIR.glob(pattern):
            code, output = run_cmd(f'python -m py_compile "{f}"')
            if code != 0:
                print(f"❌ Ошибка синтаксиса в {f.name}:")
                print(output)
                return 1
    print("   ✅ Синтаксис OK")
    
    # 2. Проверка миграций
    print("\n📋 2/5 Проверка миграций...")
    code, output = run_cmd('python scripts/check_migrations.py')
    print(output)
    if 'Отсутствующие таблицы' in output:
        print("❌ Есть непримененные миграции!")
        return 1
    
    # 3. Git status
    print("\n📋 3/5 Проверка изменений...")
    code, output = run_cmd('git status --porcelain')
    
    if not output.strip():
        print("   ℹ️  Нет изменений для коммита")
        return 0
    
    changed_files = [l.strip() for l in output.strip().split('\n') if l.strip()]
    print(f"   📝 Изменено файлов: {len(changed_files)}")
    for f in changed_files[:10]:
        print(f"      {f}")
    if len(changed_files) > 10:
        print(f"      ... и ещё {len(changed_files) - 10}")
    
    # 4. Коммит
    print("\n📋 4/5 Создание коммита...")
    
    commit_msg = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else None
    
    if not commit_msg:
        commit_msg = input("   Введи сообщение коммита: ").strip()
    
    if not commit_msg:
        commit_msg = "update: автоматический деплой"
    
    run_cmd('git add -A')
    code, output = run_cmd(f'git commit -m "{commit_msg}"')
    
    if code != 0 and 'nothing to commit' not in output:
        print(f"❌ Ошибка коммита: {output}")
        return 1
    
    print(f"   ✅ Коммит создан: {commit_msg}")
    
    # 5. Push
    print("\n📋 5/5 Отправка в GitHub...")
    code, output = run_cmd('git push origin main')
    
    if code != 0:
        print(f"❌ Ошибка push: {output}")
        return 1
    
    print("   ✅ Отправлено в GitHub!")
    
    print("\n" + "=" * 50)
    print("🎉 Деплой завершён успешно!")
    print("\nСледующие шаги:")
    print("1. Перезапусти бота на сервере (если есть)")
    print("2. Или запусти локально: python main.py")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
