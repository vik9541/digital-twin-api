# Viktor System - Структура Проектов

## 🎯 Основной проект: digital-twin-api

**URL:** https://api.97v.ru  
**Технология:** FastAPI / Python  
**Версия:** 2.0.0  
**Статус:** ✅ АКТИВЕН (Production)

### Репозиторий
- **GitHub:** vik9541/digital-twin-api
- **Локальный путь:** `C:\Users\9541\digital-twin-api`

---

## 🛑 Неиспользуемые / На паузе

### 97k-backend (NestJS)
- **Статус:** НЕ ИСПОЛЬЗУЕТСЯ
- **Причина:** Отдельный проект на паузе
- **Не путать с Viktor System!**

---

## 🏗️ Инфраструктура

### DigitalOcean Kubernetes
- **Cluster ID:** `3fbf1852-b6c2-437f-b86e-9aefe81d2ec6`
- **Region:** NYC2 (New York)
- **LoadBalancer IP:** `138.197.242.93`

### K8s Namespaces
- `production` - Viktor System API
- `super-brain` - Super Brain Digital Twin
- `shop-97k-prod` - 97k магазин
- `argocd` - CI/CD

### Важные K8s Ресурсы
```yaml
# Service для api.97v.ru
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: production
spec:
  selector:
    app: digital-twin-api
  ports:
    - port: 8000
      targetPort: 8000
```

---

## 🤖 Telegram Боты

| Бот | Username | Назначение |
|-----|----------|------------|
| Personal Bot | @LavrentevViktor_bot | Личный бот Виктора |
| Router Bot | @viktor_automation_bot | Маршрутизация задач |
| Helper Bot | @viktor_uncertain_helper_bot | Обработка неопределенностей |

---

## 📚 Связанные Репозитории

| Репозиторий | Описание | Статус |
|-------------|----------|--------|
| digital-twin-api | Viktor System API | ✅ Активен |
| super-brain-digital-twin | AI Brain | ✅ Активен |
| 97k-backend | NestJS backend | ⏸️ Пауза |
| 97k-frontend | React frontend | ⏸️ Пауза |
| 97k-database | Схемы БД | ⏸️ Пауза |
| 97k-infrastructure | K8s манифесты | 🔄 Справочный |
| 97k-n8n-workflows | n8n автоматизации | 🔄 Справочный |
| 97k-97v-specs | Спецификации | 📝 Документация |

---

## 🔐 Учетные данные

**Файл с credentials:** Хранится локально (не в Git)  
См. отдельный защищенный документ для токенов и паролей.

---

## 📅 Обновлено
- **Дата:** 2025-01-29
- **Автор:** AI Agent (GitHub Copilot)
