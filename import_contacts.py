"""
Скрипт импорта контактов в Outlook через Microsoft Graph API

Использование:
1. Экспортируйте контакты из Outlook/iCloud в CSV
2. Запустите: python import_contacts.py contacts.csv

Поддерживаемые форматы CSV:
- Outlook CSV (русский/английский)
- iCloud vCard экспорт (конвертированный в CSV)
- Google Contacts CSV
"""

import httpx
import csv
import os
import sys
import json
from pathlib import Path

# Microsoft Graph API
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

def get_token():
    """Получить токен из переменной окружения или .env файла"""
    token = os.environ.get("MS_ACCESS_TOKEN")
    
    if not token:
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MS_ACCESS_TOKEN="):
                        token = line.split("=", 1)[1].strip()
                        break
    
    if not token:
        print("❌ Ошибка: MS_ACCESS_TOKEN не найден")
        print("Установите переменную окружения или добавьте в .env файл")
        sys.exit(1)
    
    return token

def parse_csv_contact(row, headers):
    """Парсинг строки CSV в формат контакта Graph API"""
    
    # Маппинг полей (поддержка разных форматов CSV, включая русский Outlook)
    field_mapping = {
        # Имя
        "given_name": ["First Name", "Имя", "Given Name", "givenName", "first_name"],
        "surname": ["Last Name", "Фамилия", "Family Name", "surname", "last_name"],
        "display_name": ["Display Name", "Отображаемое имя", "Name", "displayName", "Full Name", "ФИО"],
        "middle_name": ["Middle Name", "Отчество", "middleName"],
        
        # Email
        "email1": ["E-mail Address", "Email", "E-mail", "email", "Email 1 - Value", "Primary Email", "Электронная почта", "Адрес эл. почты"],
        "email2": ["E-mail 2 Address", "Email 2", "Email 2 - Value", "Дополнительный email", "Адрес 2 эл. почты"],
        "email3": ["E-mail 3 Address", "Email 3", "Адрес 3 эл. почты"],
        
        # Телефоны
        "mobile": ["Mobile Phone", "Мобильный телефон", "Mobile", "Phone 1 - Value", "Сотовый телефон", "Телефон переносной"],
        "home_phone": ["Home Phone", "Домашний телефон", "Home", "Phone 2 - Value", "Телефон дом. 2"],
        "business_phone": ["Business Phone", "Рабочий телефон", "Work", "Company Main Phone", "Основной телефон организации"],
        "other_phone": ["Other Phone", "Другой телефон"],
        "main_phone": ["Primary Phone", "Основной телефон"],
        
        # Компания
        "company": ["Company", "Организация", "Organization", "Компания", "Organization 1 - Name"],
        "job_title": ["Job Title", "Должность", "Title", "Organization 1 - Title"],
        "department": ["Department", "Отдел"],
        
        # Адрес (домашний)
        "home_street": ["Street", "Улица", "Home Street", "Address 1 - Street", "Улица (дом. адрес)"],
        "home_city": ["City", "Город", "Home City", "Address 1 - City", "Город (дом. адрес)"],
        "home_state": ["State", "Область", "Home State", "Address 1 - Region", "Область (дом. адрес)"],
        "home_postal": ["Postal Code", "Индекс", "Home Postal Code", "Address 1 - Postal Code", "Почтовый код (дом.)"],
        "home_country": ["Country", "Страна", "Home Country", "Address 1 - Country", "Страна или регион (дом. адрес)"],
        
        # Адрес (рабочий)
        "work_street": ["Business Street", "Улица (раб. адрес)"],
        "work_city": ["Business City", "Город (раб. адрес)"],
        "work_state": ["Business State", "Область (раб. адрес)"],
        "work_postal": ["Business Postal Code", "Индекс (раб. адрес)"],
        "work_country": ["Business Country", "Страна или регион (раб. адрес)"],
        
        # Заметки
        "notes": ["Notes", "Заметки", "Description"]
    }
    
    def get_field(field_names):
        """Получить значение поля по списку возможных названий"""
        for name in field_names:
            if name in headers:
                idx = headers.index(name)
                if idx < len(row) and row[idx].strip():
                    return row[idx].strip()
        return None
    
    # Собираем данные контакта
    contact = {}
    
    # Имя - в русском Outlook поле "Имя" часто содержит полное имя
    given_name = get_field(field_mapping["given_name"])
    surname = get_field(field_mapping["surname"])
    display_name = get_field(field_mapping["display_name"])
    middle_name = get_field(field_mapping["middle_name"])
    
    # Если есть "Имя" но нет "Фамилия", то "Имя" может содержать полное имя
    if given_name and not surname and not display_name:
        # Попробуем разбить на части
        parts = given_name.split()
        if len(parts) >= 2:
            display_name = given_name
            given_name = parts[0]
            surname = parts[-1] if len(parts) == 2 else " ".join(parts[1:])
        else:
            display_name = given_name
    
    if given_name:
        contact["givenName"] = given_name
    if surname:
        contact["surname"] = surname
    if middle_name:
        contact["middleName"] = middle_name
    
    # Display name
    if display_name:
        contact["displayName"] = display_name
    elif given_name or surname:
        parts = [given_name, middle_name, surname]
        contact["displayName"] = " ".join(p for p in parts if p)
    
    # Email
    emails = []
    email1 = get_field(field_mapping["email1"])
    email2 = get_field(field_mapping["email2"])
    email3 = get_field(field_mapping.get("email3", []))
    
    if email1 and "@" in email1:
        emails.append({"address": email1, "name": contact.get("displayName", email1)})
    if email2 and "@" in email2:
        emails.append({"address": email2, "name": contact.get("displayName", email2)})
    if email3 and "@" in email3:
        emails.append({"address": email3, "name": contact.get("displayName", email3)})
    
    if emails:
        contact["emailAddresses"] = emails
    
    # Телефоны
    mobile = get_field(field_mapping["mobile"])
    home_phone = get_field(field_mapping["home_phone"])
    business_phone = get_field(field_mapping["business_phone"])
    other_phone = get_field(field_mapping.get("other_phone", []))
    main_phone = get_field(field_mapping.get("main_phone", []))
    
    # Нормализация телефона - берём первый непустой
    phone = mobile or other_phone or main_phone or home_phone
    
    if phone:
        contact["mobilePhone"] = phone
    if home_phone and home_phone != phone:
        contact["homePhones"] = [home_phone]
    if business_phone:
        contact["businessPhones"] = [business_phone]
    
    # Компания
    company = get_field(field_mapping["company"])
    job_title = get_field(field_mapping["job_title"])
    department = get_field(field_mapping.get("department", []))
    
    if company:
        contact["companyName"] = company
    if job_title:
        contact["jobTitle"] = job_title
    if department:
        contact["department"] = department
    
    # Адрес (домашний)
    home_street = get_field(field_mapping.get("home_street", []))
    home_city = get_field(field_mapping.get("home_city", []))
    home_state = get_field(field_mapping.get("home_state", []))
    home_postal = get_field(field_mapping.get("home_postal", []))
    home_country = get_field(field_mapping.get("home_country", []))
    
    if any([home_street, home_city, home_state, home_postal, home_country]):
        contact["homeAddress"] = {
            "street": home_street,
            "city": home_city,
            "state": home_state,
            "postalCode": home_postal,
            "countryOrRegion": home_country
        }
        contact["homeAddress"] = {k: v for k, v in contact["homeAddress"].items() if v}
    
    # Адрес (рабочий)
    work_street = get_field(field_mapping.get("work_street", []))
    work_city = get_field(field_mapping.get("work_city", []))
    work_state = get_field(field_mapping.get("work_state", []))
    work_postal = get_field(field_mapping.get("work_postal", []))
    work_country = get_field(field_mapping.get("work_country", []))
    
    if any([work_street, work_city, work_state, work_postal, work_country]):
        contact["businessAddress"] = {
            "street": work_street,
            "city": work_city,
            "state": work_state,
            "postalCode": work_postal,
            "countryOrRegion": work_country
        }
        contact["businessAddress"] = {k: v for k, v in contact["businessAddress"].items() if v}
    
    # Заметки
    notes = get_field(field_mapping["notes"])
    if notes:
        contact["personalNotes"] = notes
    
    return contact

def create_contact(token, contact_data):
    """Создать контакт через Graph API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = httpx.post(
        f"{GRAPH_API_BASE}/me/contacts",
        headers=headers,
        json=contact_data,
        timeout=30
    )
    
    return response

def import_contacts_from_csv(csv_path):
    """Импорт контактов из CSV файла"""
    
    token = get_token()
    
    print(f"\n📂 Чтение файла: {csv_path}")
    
    # Определяем кодировку
    encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']
    content = None
    
    for encoding in encodings:
        try:
            with open(csv_path, 'r', encoding=encoding) as f:
                content = f.read()
                break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print("❌ Не удалось определить кодировку файла")
        return
    
    # Парсим CSV
    lines = content.strip().split('\n')
    
    # Определяем разделитель
    first_line = lines[0]
    delimiter = ',' if first_line.count(',') > first_line.count(';') else ';'
    
    reader = csv.reader(lines, delimiter=delimiter)
    rows = list(reader)
    
    if len(rows) < 2:
        print("❌ Файл пустой или содержит только заголовки")
        return
    
    headers = rows[0]
    data_rows = rows[1:]
    
    print(f"📊 Найдено контактов: {len(data_rows)}")
    print(f"📋 Колонки: {', '.join(headers[:5])}{'...' if len(headers) > 5 else ''}")
    print()
    
    # Импорт
    success_count = 0
    error_count = 0
    
    for i, row in enumerate(data_rows, 1):
        contact_data = parse_csv_contact(row, headers)
        
        # Пропускаем пустые контакты
        if not contact_data.get("displayName") and not contact_data.get("givenName"):
            print(f"⏭️  [{i}/{len(data_rows)}] Пропущен (нет имени)")
            continue
        
        name = contact_data.get("displayName", contact_data.get("givenName", "Без имени"))
        
        try:
            response = create_contact(token, contact_data)
            
            if response.status_code in [200, 201]:
                print(f"✅ [{i}/{len(data_rows)}] {name}")
                success_count += 1
            else:
                error = response.json().get("error", {}).get("message", response.text)
                print(f"❌ [{i}/{len(data_rows)}] {name}: {error[:50]}")
                error_count += 1
        except Exception as e:
            print(f"❌ [{i}/{len(data_rows)}] {name}: {str(e)[:50]}")
            error_count += 1
    
    # Итоги
    print()
    print("=" * 50)
    print(f"✅ Успешно импортировано: {success_count}")
    print(f"❌ Ошибок: {error_count}")
    print(f"⏭️  Пропущено: {len(data_rows) - success_count - error_count}")
    print("=" * 50)

def main():
    print("=" * 50)
    print("  ИМПОРТ КОНТАКТОВ В OUTLOOK")
    print("  Microsoft Graph API")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nИспользование:")
        print("  python import_contacts.py <путь_к_csv>")
        print("\nПример:")
        print("  python import_contacts.py contacts.csv")
        print("  python import_contacts.py C:\\Users\\Viktor\\contacts.csv")
        print()
        print("Как получить CSV:")
        print("  1. Outlook: Файл → Экспорт → CSV")
        print("  2. iCloud: icloud.com/contacts → ⚙️ → Экспорт vCard → конвертировать в CSV")
        print("  3. Google: contacts.google.com → Экспорт → CSV")
        return
    
    csv_path = sys.argv[1]
    
    if not os.path.exists(csv_path):
        print(f"❌ Файл не найден: {csv_path}")
        return
    
    import_contacts_from_csv(csv_path)

if __name__ == "__main__":
    main()
