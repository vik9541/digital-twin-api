#!/usr/bin/env python3
"""
Скрипт для удаления дубликатов контактов из Outlook через Microsoft Graph API
"""

import httpx
import os
from pathlib import Path
from collections import defaultdict

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


def get_all_contacts(client: httpx.Client) -> list[dict]:
    """Получить все контакты с пагинацией"""
    contacts = []
    url = f"{GRAPH_API_URL}/me/contacts?$top=999&$select=id,displayName,givenName,surname,emailAddresses,mobilePhone,businessPhones"
    
    while url:
        response = client.get(url)
        if response.status_code != 200:
            print(f"Ошибка получения контактов: {response.status_code}")
            print(response.text[:500])
            break
        
        data = response.json()
        contacts.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
        
        print(f"Загружено контактов: {len(contacts)}")
    
    return contacts


def delete_contact(client: httpx.Client, contact_id: str) -> bool:
    """Удалить контакт по ID"""
    response = client.delete(f"{GRAPH_API_URL}/me/contacts/{contact_id}")
    return response.status_code == 204


def get_contact_key(contact: dict) -> str:
    """Создать ключ для идентификации дубликатов"""
    # Используем displayName как основной ключ
    name = contact.get("displayName", "").strip().lower()
    
    # Добавляем первый email если есть
    emails = contact.get("emailAddresses", [])
    email = emails[0].get("address", "").lower() if emails else ""
    
    # Добавляем телефон
    phone = contact.get("mobilePhone", "") or ""
    if not phone:
        phones = contact.get("businessPhones", [])
        phone = phones[0] if phones else ""
    
    # Ключ: имя + email (если есть)
    if email:
        return f"{name}|{email}"
    return name


def main():
    ACCESS_TOKEN = get_token()
    if not ACCESS_TOKEN:
        print("Ошибка: MS_ACCESS_TOKEN не найден в .env")
        return
    
    print("Удаление дубликатов контактов из Outlook")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    with httpx.Client(headers=headers, timeout=30.0) as client:
        # Получаем все контакты
        print("\n1. Загрузка контактов...")
        contacts = get_all_contacts(client)
        print(f"Всего контактов: {len(contacts)}")
        
        # Группируем по ключу
        print("\n2. Поиск дубликатов...")
        groups = defaultdict(list)
        for contact in contacts:
            key = get_contact_key(contact)
            if key:  # Пропускаем пустые ключи
                groups[key].append(contact)
        
        # Находим дубликаты
        duplicates_to_delete = []
        for key, group in groups.items():
            if len(group) > 1:
                # Оставляем первый, остальные на удаление
                duplicates_to_delete.extend(group[1:])
        
        print(f"Найдено дубликатов: {len(duplicates_to_delete)}")
        
        if not duplicates_to_delete:
            print("\nДубликатов не найдено!")
            return
        
        # Показываем примеры
        print("\nПримеры дубликатов (первые 10):")
        for dup in duplicates_to_delete[:10]:
            print(f"  - {dup.get('displayName', 'Без имени')}")
        
        # Удаляем дубликаты
        print(f"\n3. Удаление {len(duplicates_to_delete)} дубликатов...")
        deleted = 0
        errors = 0
        
        for i, contact in enumerate(duplicates_to_delete):
            success = delete_contact(client, contact["id"])
            if success:
                deleted += 1
            else:
                errors += 1
            
            if (i + 1) % 100 == 0:
                print(f"Удалено: {deleted}, ошибок: {errors}")
        
        print("\n" + "=" * 50)
        print(f"Готово!")
        print(f"Удалено дубликатов: {deleted}")
        print(f"Ошибок: {errors}")
        print(f"Осталось контактов: {len(contacts) - deleted}")


if __name__ == "__main__":
    main()
