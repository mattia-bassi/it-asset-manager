# Architecture — IT Asset Manager v2.7.5

## Overview

IT Asset Manager is a self-hosted web application for managing IT assets, assignments, personnel, and compliance. It follows a classic three-tier architecture deployed as Docker containers on a macvlan network.

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                       Local Network                          │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │   asset-app    │  │ asset-mariadb  │  │  asset-redis  │  │
│  │                │  │                │  │               │  │
│  │  FastAPI +     │  │  MariaDB 10.11 │  │  Redis 7      │  │
│  │  React SPA     │──│  17 tables     │  │  Rate limit + │  │
│  │  125+ endpoints│  │  utf8mb4       │  │  Sessions     │  │
│  │                │  │                │  │               │  │
│  │  Port 8000     │  │  Port 3306     │  │  Port 6379    │  │
│  └────────────────┘  └────────────────┘  └───────────────┘  │
│          │                                                   │
│  ┌────────────────┐                                          │
│  │  compliance    │  One-shot container                      │
│  │  26 tests      │  ISO 27001 auditor/auditee separation   │
│  │  JSON + PDF    │  Runs on demand via SSH                  │
│  └────────────────┘                                          │
│                                                              │
│  ┌────────────────┐                                          │
│  │  setup-wizard  │  First-run only                          │
│  │  Flask + UI    │  8 screens, 22 API steps                 │
│  │  Port 8080     │  Auto-removes after install              │
│  └────────────────┘                                          │
└──────────────────────────────────────────────────────────────┘
```

## Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI (Python 3.12) | REST API, async support |
| ORM | SQLAlchemy 2.0 | Database abstraction, relationships |
| Validation | Pydantic v2 | Request/response schema validation |
| Migrations | Alembic | Schema versioning and upgrades |
| Auth | JWT HS256 (python-jose) | Stateless authentication, 8h expiry |
| Password | Argon2id (passlib) | OWASP-recommended password hashing |
| Encryption | Fernet AES-128-CBC | Encryption at rest (SIM PIN/PUK, audit logs) |
| Rate Limiting | slowapi + Redis | Brute-force protection on login endpoint |
| WSGI | uvicorn | Production ASGI server |

### Frontend

| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | React 19 | Component-based SPA |
| Language | TypeScript | Type safety |
| Styling | TailwindCSS 3 | Utility-first responsive layout |
| Charts | Recharts | Dashboard visualizations |
| HTTP Client | Axios | API communication |
| Routing | React Router v6 | Client-side navigation |
| Build | Vite | Fast build toolchain |

### Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| Database | MariaDB 10.11 | Relational data storage |
| Cache | Redis 7 (Alpine) | Rate limiting, session management |
| Containers | Docker + Docker Compose | Deployment and isolation |
| Networking | macvlan | Dedicated IPs per service on LAN |
| SSL | Self-signed certificates | HTTPS in production (auto-generated) |

## Application Layers

### Request Flow

```
Browser → HTTPS/HTTP → FastAPI (uvicorn)
                           │
                           ├── Security Headers Middleware (OWASP)
                           ├── CORS Middleware
                           ├── JWT Authentication (deps.py)
                           ├── Rate Limiting (slowapi)
                           │
                           ├── Router Layer (/api/*)
                           │   └── Request validation (Pydantic)
                           │
                           ├── Service Layer (business logic)
                           │   ├── Audit logging (every CRUD op)
                           │   └── Encryption (SIM PIN/PUK)
                           │
                           └── Data Layer (SQLAlchemy → MariaDB)
```

### Directory Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI entry + SPA routing
│   ├── db/session.py        # Database session management
│   ├── core/
│   │   ├── config.py        # Pydantic Settings (from .env)
│   │   ├── security.py      # JWT + Argon2id password hashing
│   │   ├── log_encryption.py # Fernet encryption for audit logs
│   │   ├── rate_limit.py    # slowapi + Redis configuration
│   │   └── cors.py          # CORS origins configuration
│   ├── models/              # SQLAlchemy ORM models (17 tables)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic layer
│   ├── routers/             # API endpoint definitions (125+)
│   └── middleware/
│       └── security_headers.py  # 7 OWASP security headers
├── alembic/                 # Database migrations
├── entrypoint.sh            # Boot script (SSL detect + Alembic)
└── Dockerfile

frontend/
├── src/
│   ├── pages/               # 14 application pages
│   ├── components/          # Reusable UI components
│   ├── api.ts               # Axios HTTP client + getApiError() helper
│   └── App.tsx              # Router + layout
└── dist/                    # Production build (served by FastAPI)
```

## Networking

### Macvlan Architecture

Each container receives a dedicated IP address on the local network, appearing as an independent device. This allows direct browser access without port forwarding.

```
Host Server (e.g., 10.20.0.50)
    │
    ├── macvlan network (bridge to physical NIC)
    │   ├── asset-app       → <app-ip>:8000
    │   ├── asset-mariadb   → <db-ip>:3306
    │   ├── asset-redis     → <redis-ip>:6379
    │   └── compliance      → dynamic (one-shot)
    │
    └── host network
        └── setup-wizard    → <host-ip>:8080 (first run only)
```

**Known limitation:** The host machine cannot directly communicate with macvlan containers. Health checks use `docker exec` internally.

## Security Architecture

### Authentication Flow

```
POST /api/auth/login (form-urlencoded)
    │
    ├── Rate limit check (5 attempts/minute via Redis)
    ├── Username lookup (SQLAlchemy)
    ├── Password verify (Argon2id)
    │
    └── JWT token generation
        ├── Payload: {sub: username, role: admin|operator|user}
        ├── Algorithm: HS256
        ├── Expiry: 8 hours
        └── Secret: from .env (64-byte random)
```

### RBAC (Role-Based Access Control)

| Role | Scope | Description |
|------|-------|-------------|
| Admin | Full access | All CRUD operations, user management, compliance |
| Operator | Operational access | Asset/assignment management, no user admin |
| User | Self-service only | View own assignments, GDPR rights, change password |

### Encryption

| Data | Method | Key Source |
|------|--------|------------|
| Passwords | Argon2id hash | N/A (one-way) |
| SIM PIN/PUK | Fernet AES-128-CBC | `AUDIT_LOG_ENCRYPTION_KEY` in .env |
| Audit log details | Fernet AES-128-CBC | Same key |
| HTTPS traffic | TLS 1.2+ | Self-signed or CA certificate |

### Security Headers (Middleware)

Every response includes 7 OWASP-recommended headers:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self' ...`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Strict-Transport-Security: max-age=31536000` (HTTPS only)

## Compliance Architecture

The compliance system follows ISO 27001 Clause 9.2 — the auditor must be independent from the auditee.

```
┌───────────────────┐         HTTP         ┌───────────────────┐
│ asset-compliance  │ ──────────────────▶  │    asset-app      │
│ (auditor)         │                      │    (auditee)      │
│                   │ ◀──────────────────  │                   │
│ 26 tests          │      Responses       │ Serves responses  │
│ JSON + PDF report │                      │                   │
└───────────────────┘                      └───────────────────┘
         │
         ▼
   data/compliance/
   ├── latest_report.json    (read by app UI)
   └── compliance_report_*.pdf
```

## Bootstrap Wizard

The wizard is a temporary Flask application that automates first-time setup:

- Runs as a Docker container with `network_mode: host`
- Accesses Docker socket to create/manage application containers
- Generates `docker-compose.yml` and `backend/.env` from user input
- Executes 22 installation steps (network, DB, schema, seed, admin, frontend)
- Creates tables via raw DDL (not Alembic) for reliability, then marks Alembic head
- Self-removes after installation

---

*Document Version: 1.0 — March 2026*
