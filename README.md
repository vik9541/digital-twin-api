# Viktor Digital Twin API

**URL:** https://api.97v.ru  
**Status:** Production  

## Quick Start

# окальный запуск
docker-compose up -d

# роверка здоровья
curl https://api.97v.ru/health

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Health check |
| /api/... | * | API routes |

## Infrastructure

- **Platform:** DigitalOcean Kubernetes
- **Region:** NYC2
- **SSL:** Let's Encrypt (auto)

## Documentation

- docs/PROJECT_STRUCTURE.md

## Related Projects

- super-brain-digital-twin - AI Brain система
- viktor-ai-context - Т и контекст
