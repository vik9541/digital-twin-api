import httpx
import os

token = os.environ.get("MS_ACCESS_TOKEN", "")

if not token:
    print("Ошибка: MS_ACCESS_TOKEN не установлен")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Get user info
print("=" * 50)
print("ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ")
print("=" * 50)
r = httpx.get("https://graph.microsoft.com/v1.0/me", headers=headers)
if r.status_code == 200:
    user = r.json()
    print(f"Имя: {user.get('displayName')}")
    print(f"Email: {user.get('mail') or user.get('userPrincipalName')}")
else:
    print(f"Ошибка: {r.status_code} - {r.text}")
    exit(1)

# Get contacts
print("\n" + "=" * 50)
print("КОНТАКТЫ")
print("=" * 50)
r = httpx.get(
    "https://graph.microsoft.com/v1.0/me/contacts",
    headers=headers,
    params={"$top": 50, "$orderby": "displayName"}
)

if r.status_code == 200:
    data = r.json()
    contacts = data.get("value", [])
    print(f"Всего контактов: {len(contacts)}\n")
    
    for i, c in enumerate(contacts, 1):
        name = c.get("displayName", "Без имени")
        emails = c.get("emailAddresses", [])
        email = emails[0].get("address") if emails else "нет email"
        phone = c.get("mobilePhone") or (c.get("businessPhones", []) or [""])[0] or "нет телефона"
        company = c.get("companyName") or ""
        
        print(f"{i}. {name}")
        print(f"   📧 {email}")
        print(f"   📱 {phone}")
        if company:
            print(f"   🏢 {company}")
        print()
else:
    print(f"Ошибка: {r.status_code} - {r.text}")
