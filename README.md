# Viktor Digital Twin API

**URL:** https://api.97v.ru  
**Status:** ✅ Production  

## Quick Start

```bash
# Локальный запуск
docker-compose up -d

# Проверка здоровья
curl https://api.97v.ru/health
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/...` | * | API routes |

## Infrastructure

- **Platform:** DigitalOcean Kubernetes
- **Region:** NYC2
- **SSL:** Let's Encrypt (auto)

## Documentation

- [Структура проектов](docs/PROJECT_STRUCTURE.md)

## Related Projects

- [super-brain-digital-twin](https://github.com/vik9541/super-brain-digital-twin)

---

> ⚠️ **Important:** Не путать с 97k-backend (NestJS) - это отдельный проект на паузе.
