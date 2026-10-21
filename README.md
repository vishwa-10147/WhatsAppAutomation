# WhatsApp Automation Platform

A multi-tenant platform for official WhatsApp Business Cloud API messaging, visual workflow automation, contact/conversation management, scheduling, and AI-assisted support.

## Status

**Phase 1-3 Foundation Complete**: Multi-tenant auth, WhatsApp Cloud API integration (mock + production), workflow database schema, webhook processing.

**Next**: Phase 3 continued - Workflow execution engine, React Flow visual editor, Phase 4 Contacts/Inbox UI.

## Quick Start (Docker)

```bash
# 1. Clone and configure
git clone <repo>
cd WhatsAppAutomation
cp .env.example .env
# Edit .env with your secrets

# 2. Start stack
docker compose up --build -d

# 3. Run migrations
docker compose exec api alembic upgrade head

# 4. Access
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│    API      │────▶│  PostgreSQL │
│  (React)    │     │  (FastAPI)  │     │             │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐     ┌─────────────┐
                    │   Redis     │────▶│  Workers    │
                    │  (Queue)    │     │  (Celery)   │
                    └─────────────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │  WhatsApp   │
                    │  Cloud API  │
                    └─────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query, React Router |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.x, Pydantic 2, Alembic |
| Database | PostgreSQL 16 |
| Queue | Redis 7, Celery 5 |
| Auth | JWT, bcrypt, Fernet encryption |
| WhatsApp | Meta Cloud API v20.0 |
| Deployment | Docker Compose, Nginx |

## Project Structure

```
whatsapp-automation/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/          # REST endpoints
│   │   │   └── webhooks/        # WhatsApp webhooks
│   │   ├── core/                # Config, security, logging
│   │   ├── db/                  # Database session
│   │   ├── integrations/
│   │   │   └── whatsapp/        # WhatsApp providers
│   │   ├── models/              # SQLAlchemy models
│   │   ├── repositories/        # Data access
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # Business logic
│   │   ├── workers/             # Celery workers
│   │   └── main.py
│   ├── alembic/                 # Migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client
│   │   ├── components/
│   │   │   ├── ui/              # Reusable UI components
│   │   │   └── layout/          # Sidebar, Header
│   │   ├── features/            # Feature pages
│   │   ├── hooks/               # React hooks
│   │   ├── types/               # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── README.md
├── PLAN.md
├── ARCHITECTURE.md
└── SECURITY.md
```

## Features Implemented

### Phase 1: Foundation
- ✅ Multi-tenant organization support
- ✅ JWT authentication with org-scoped tokens
- ✅ User registration/login/organization creation
- ✅ Role-based access (admin/member/viewer)
- ✅ Docker Compose with health checks
- ✅ Database migrations with Alembic
- ✅ Frontend dashboard shell with sidebar navigation
- ✅ Dark/light theme support

### Phase 2: WhatsApp Integration
- ✅ Provider abstraction (mock + Cloud API)
- ✅ WhatsApp Business account management
- ✅ Encrypted credential storage (Fernet)
- ✅ Message sending: text, template, media
- ✅ Webhook verification & processing
- ✅ Inbound message & status update handling
- ✅ Contact & conversation persistence
- ✅ Message templates support

### Phase 3: Workflow Engine (Database Layer)
- ✅ Workflow definitions with versioning
- ✅ Node/edge graph schema (JSON)
- ✅ Execution tracking with node-level detail
- ✅ Scheduled jobs (cron + one-time)
- ✅ Idempotency keys for safe retries

## API Endpoints

### Auth
- `POST /api/v1/auth/register` - Register user + organization
- `POST /api/v1/auth/login` - Login, returns JWT
- `GET /api/v1/auth/me` - Current user + organizations
- `POST /api/v1/auth/switch-organization` - Switch active org

### WhatsApp Accounts
- `POST /api/v1/accounts` - Create account
- `GET /api/v1/accounts` - List accounts
- `GET /api/v1/accounts/{id}` - Get account
- `PATCH /api/v1/accounts/{id}` - Update account
- `DELETE /api/v1/accounts/{id}` - Delete account
- `POST /api/v1/accounts/{id}/send/text` - Send text message
- `POST /api/v1/accounts/{id}/send/template` - Send template message
- `POST /api/v1/accounts/{id}/send/media` - Send media message
- `POST /api/v1/accounts/{id}/upload-media` - Upload media

### Webhooks
- `GET /api/v1/webhooks/whatsapp` - Verify webhook
- `POST /api/v1/webhooks/whatsapp` - Receive events

### Health
- `GET /api/v1/health` - Basic health
- `GET /api/v1/ready` - Readiness with dependency checks

## Development

### Backend Tests
```bash
docker compose exec api pytest -v
```

### Frontend Tests
```bash
docker compose exec frontend npm test
```

### Linting
```bash
# Backend
docker compose exec api ruff check .

# Frontend
docker compose exec frontend npm run lint
```

### Database Migrations
```bash
# Create new migration
docker compose exec api alembic revision --autogenerate -m "description"

# Apply migrations
docker compose exec api alembic upgrade head

# Rollback
docker compose exec api alembic downgrade -1
```

## Configuration

Key environment variables (see `.env.example`):

| Variable | Description |
|----------|-------------|
| `APP_SECRET_KEY` | JWT signing key (min 32 chars) |
| `ENCRYPTION_KEY` | Fernet key for credential encryption |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `WHATSAPP_MOCK_MODE` | Use mock provider (dev) |
| `WHATSAPP_APP_ID` | Meta App ID (prod) |
| `WHATSAPP_APP_SECRET` | Meta App Secret (prod) |
| `OPENAI_API_KEY` | For AI assistant (Phase 5) |

## Production Deployment

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for:
- Nginx reverse proxy with TLS
- Managed PostgreSQL/Redis
- Secrets management
- Backup/restore procedures
- Monitoring & alerting

## Security

See [SECURITY.md](./SECURITY.md) for:
- Threat model
- Data protection
- Authentication/authorization
- Webhook security
- Encryption details
- Compliance considerations

## License

Proprietary - All rights reserved.