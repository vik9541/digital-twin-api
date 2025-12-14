#!/usr/bin/env python3
"""
Скрипт для импорта контактов из CSV (экспорт Outlook) в Outlook.com через Microsoft Graph API
"""

import csv
import sys
import httpx
import os
from pathlib import Path
from io import StringIO

GRAPH_API_URL = "https://graph.microsoft.com/v1.0"


def get_token():
    """Получить токен из .env файла"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MS_ACCESS_TOKEN="):
                    return line.split("=", 1)[1].strip()
    return os.environ.get("MS_ACCESS_TOKEN")


def read_csv_safely(csv_path: Path) -> str:
    """Читает CSV файл с обработкой BOM и кодировки"""
    with open(csv_path, 'rb') as f:
        raw = f.read()
    
    # Удаляем BOM если есть
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    
    # Декодируем с заменой проблемных символов
    return raw.decode('utf-8', errors='replace')


def parse_csv_contact(row: dict) -> dict | None:
    """Преобразует строку CSV в формат Graph API"""
    
    # Получаем имя - в Outlook CSV полное имя часто в поле "Имя"
    given_name = row.get('Имя', '').strip()
    surname = row.get('Фамилия', '').strip()
    middle_name = row.get('Отчество', '').strip()
    
    # Если фамилия пустая, а имя содержит пробелы - это полное имя
    # Формат: "Фамилия Имя" или "Фамилия Имя Отчество"
    if not surname and ' ' in given_name:
        parts = given_name.split()
        if len(parts) >= 2:
            surname = parts[0]
            given_name = parts[1]
            if len(parts) > 2:
                middle_name = ' '.join(parts[2:])
    
    # Пропускаем контакты без имени
    if not given_name and not surname:
        return None
    
    # Формируем displayName
    display_parts = [p for p in [surname, given_name, middle_name] if p]
    display_name = ' '.join(display_parts)
    
    contact = {
        "displayName": display_name,
    }
    
    if given_name:
        contact["givenName"] = given_name
    if surname:
        contact["surname"] = surname
    if middle_name:
        contact["middleName"] = middle_name
    
    # Организация
    if company := row.get('Организация', '').strip():
        contact['companyName'] = company
    
    # Должность
    if job := row.get('Должность', '').strip():
        contact['jobTitle'] = job
    
    # Отдел
    if dept := row.get('Отдел', '').strip():
        contact['department'] = dept
    
    # Телефоны
    business_phones = []
    home_phones = []
    
    if mobile := row.get('Телефон переносной', '').strip():
        contact['mobilePhone'] = mobile
    
    if work_phone := row.get('Рабочий телефон', '').strip():
        business_phones.append(work_phone)
    if work_phone2 := row.get('Телефон раб. 2', '').strip():
        business_phones.append(work_phone2)
    
    if home_phone := row.get('Домашний телефон', '').strip():
        home_phones.append(home_phone)
    if home_phone2 := row.get('Телефон дом. 2', '').strip():
        home_phones.append(home_phone2)
    
    # Основной телефон - если нет мобильного
    if not contact.get('mobilePhone'):
        if main_phone := row.get('Основной телефон', '').strip():
            contact['mobilePhone'] = main_phone
    
    if business_phones:
        contact['businessPhones'] = business_phones
    if home_phones:
        contact['homePhones'] = home_phones
    
    # Email
    emails = []
    if email1 := row.get('Адрес эл. почты', '').strip():
        emails.append({"address": email1, "name": row.get('Краткое имя эл. почты', '').strip() or email1})
    if email2 := row.get('Адрес 2 эл. почты', '').strip():
        emails.append({"address": email2, "name": row.get('Краткое 2 имя эл. почты', '').strip() or email2})
    if email3 := row.get('Адрес 3 эл. почты', '').strip():
        emails.append({"address": email3, "name": row.get('Краткое 3 имя эл. почты', '').strip() or email3})
    
    if emails:
        contact['emailAddresses'] = emails
    
    # Заметки
    if notes := row.get('Заметки', '').strip():
        contact['personalNotes'] = notes
    
    # День рождения (формат: YYYY-MM-DD)
    if birthday := row.get('День рождения', '').strip():
        try:
            from datetime import datetime
            for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%m/%d/%Y']:
                try:
                    dt = datetime.strptime(birthday, fmt)
                    contact['birthday'] = dt.strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
        except:
            pass
    
    return contact


def import_contact(client: httpx.Client, contact: dict) -> tuple[bool, str]:
    """Создает контакт через Graph API"""
    try:
        response = client.post(
            f"{GRAPH_API_URL}/me/contacts",
            json=contact
        )
        
        if response.status_code == 201:
            return True, "OK"
        else:
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, str(e)


def main():
    if len(sys.argv) < 2:
        print("Использование: python import_csv.py <путь_к_csv>")
        sys.exit(1)
    
    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"Файл не найден: {csv_path}")
        sys.exit(1)
    
    ACCESS_TOKEN = get_token()
    if not ACCESS_TOKEN:
        print("Ошибка: MS_ACCESS_TOKEN не найден в .env")
        sys.exit(1)
    
    print(f"Импорт контактов из: {csv_path}")
    print(f"Токен: {ACCESS_TOKEN[:20]}...")
    
    # Читаем CSV безопасно
    print("Чтение файла...")
    content = read_csv_safely(csv_path)
    
    # Создаем клиент с авторизацией
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    errors = []
    
    with httpx.Client(headers=headers, timeout=30.0) as client:
        reader = csv.DictReader(StringIO(content))
        
        for i, row in enumerate(reader):
            contact = parse_csv_contact(row)
            
            if contact is None:
                skip_count += 1
                continue
            
            success, error = import_contact(client, contact)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
                if len(errors) < 10:
                    name = contact.get('displayName', 'Unknown')
                    errors.append(f"{name}: {error}")
            
            # Прогресс каждые 100 записей
            if (i + 1) % 100 == 0:
                print(f"Обработано: {i + 1} (успешно: {success_count}, ошибок: {fail_count}, пропущено: {skip_count})")
    
    print("\n" + "="*50)
    print(f"Импорт завершен!")
    print(f"Успешно: {success_count}")
    print(f"Ошибок: {fail_count}")
    print(f"Пропущено (нет имени): {skip_count}")
    
    if errors:
        print("\nПримеры ошибок:")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
