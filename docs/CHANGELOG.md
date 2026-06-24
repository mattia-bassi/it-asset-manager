# Changelog — IT Asset Manager

All notable changes to this project are documented in this file.

---

## v2.7.5 — June 2026

### Code Quality — Backend

**Logging refactoring (9 files):**
Replaced 20 `print()` calls with `logger.warning()` across all backend
service and router files that lacked proper logging:
`api/routes/auth.py`, `routers/assignments.py`, `routers/dashboard.py`,
`services/asset_service.py`, `services/assignment_service.py`,
`services/badge_service.py`, `services/excel_generator_service.py`,
`services/person_service.py`, `services/sim_service.py`.
Added `import logging` + `logger = logging.getLogger(__name__)`
to the 6 files that did not yet have it.

**Silent except refactoring (5 files):**
Replaced 10 bare `except: pass` and `except Exception: pass` blocks
with explicit logging:
- `core/logging.py`: file handler fallback → `logger.debug`
  (graceful degradation when log volume is not mounted)
- `core/rate_limit.py`: Retry-After parse failure → `logger.debug`
- `routers/location_types.py`: 3 audit log catch blocks → `logger.warning`
- `routers/locations.py`: 3 audit log catch blocks → `logger.warning`
- `routers/dashboard.py`: 4 query catch blocks → `logger.warning`

### Code Quality — Frontend

**Removed debug artifacts (`Assignments.tsx`):**
Removed 2 `console.log` debug statements and 1 `// DEBUG` comment
left from development of the SIM credentials feature.

**Centralized API error handling (22 files):**
Added `getApiError(error: unknown, fallback: string): string` helper
to `api.ts`. The function uses `axios.isAxiosError()` for type-safe
extraction of FastAPI `detail` fields from error responses.
Replaced all `catch (error: any)` with `catch (error: unknown)`
across 21 components, eliminating unsafe `any` typing in catch blocks.
Special case: `LetterheadTab.tsx` uses `axios.isAxiosError()` to
branch on HTTP 404 (expected — no default template) vs other errors.

### Documentation
- Updated React 18 → React 19 in `README.md`, `docs/ARCHITECTURE.md`,
  `docs/CHANGELOG.md` to match `package.json` (`react: ^19.2.0`)

### Dependencies
- `wizard/requirements.txt`: Flask `3.1.0` → `3.1.3` (patch update,
  security and bugfix release, same API)

---

## v2.7.4 — March 2026

### Bootstrap Wizard
- Complete 22-step automated installation wizard (Flask + 8-screen UI)
- Auto-detection of network interface, subnet, gateway
- Automatic IP availability check via ping scan
- Generates `docker-compose.yml` and `backend/.env` from user input
- DDL-based table creation (17 tables) for maximum reliability
- Seeds 30 asset types and default document template
- Creates admin account with Argon2id password hashing
- Multi-language support (Italian / English)
- Live progress bar, log console, and retry capability
- Configuration document download with optional password inclusion

### Compliance Container (External)
- New architecture: independent auditor container (ISO 27001 Clause 9.2)
- 26 automated compliance tests (up from 22)
- Generates JSON and PDF reports in shared volume
- Added 4 new tests: audit log structure, log rotation fields (archived_count, remaining_count), database hardening
- Two auxiliary API endpoints: `/api/compliance/encryption-check`, `/api/compliance/db-check`
- Backend rewritten: `compliance_service.py` (read-only), `compliance.py` router (6 endpoints)
- Frontend `ComplianceTab.tsx` with SSH guide, copy-to-clipboard, PDF download
- Configuration: `host_ip`, `project_path`, `ssh_user` read from `.env`

### Security Hardening
- Removed all hardcoded credentials from source code
- Removed hardcoded IP addresses from backend defaults
- Added `.mypy_cache` to `.gitignore`
- Sanitized codebase for public repository

### Documentation
- New `README.md` for GitLab (portfolio-ready)
- New `INSTALLATION.md` with complete setup guide
- New `LICENSE` (CC BY-NC-ND 4.0)
- Installation Guide PDF with glossary and configuration worksheet
- Technical documentation in `docs/` folder

---

## v2.7.3 — March 2026

### Wizard Development (Sessions 2-6)
- Migration squash: 24 migrations consolidated into single `0001_initial_v274.py`
- Schema generated from production mysqldump (not from ORM models) for accuracy
- DDL-based table creation via `docker exec mysql` stdin
- `SKIP_MIGRATIONS=true` flag for wizard installations
- Volume mounts changed to absolute host paths
- Build context kept relative (`./backend`, `./compliance`)
- Fixed `shutil.rmtree` permissions issue (Alpine container with root)
- Fixed InnoDB tablespace orphan errors (errno 184)

### Location Management
- New entities: `location_types` and `locations`
- Assets can be assigned to locations (rooms, server rooms, meeting rooms)
- Location-based assignment workflow alongside person-based assignments
- GDPR Art. 21 (Right to Object) endpoint added

---

## v2.7.2 — March 2026

### Master Setup Account
- First-run wizard: `master` account auto-created at boot
- Guided admin account creation via `/master-setup` page
- Master account permanently disabled after first admin is created
- Account hidden from user management interface

### Redis Integration
- New `asset-redis` container for rate limiting
- Moved rate limiting from in-memory to Redis-backed (persistent across restarts)
- Redis health check in Docker Compose

---

## v2.7.1 — February 2026

### Compliance Framework
- 22-test compliance suite (ISO 27001 + GDPR)
- OWASP security headers middleware (7 headers)
- Rate limiting on login endpoint (5 attempts/minute)
- Audit log encryption at rest (Fernet AES-128-CBC)
- Log rotation with configurable retention
- GDPR endpoints: Art. 15, 16, 17, 18, 20, 21
- Compliance test with PDF report generation

### Security
- JWT authentication with 8-hour expiry
- Argon2id password hashing (replaced bcrypt)
- Minimum 12-character password policy
- CORS configuration from environment variables
- Database user restricted to app container IP only

---

## v2.7.0 — February 2026

### Core Application
- Full CRUD for: Assets, People, Sites, Assignments, SIMs, Badges, Inventory, Suppliers
- Assignment workflow with PDF document generation
- SIM management with encrypted PIN/PUK
- Badge management with status tracking
- Inventory management with reorder thresholds
- Dashboard with real-time statistics and charts
- Multi-role RBAC (Admin, Operator, User)
- Audit logging on all CRUD operations
- Document template management (logo, footer)
- Excel export for assets

### Frontend
    - React 19 SPA with TypeScript
- 14 application pages
- Bootstrap 5 responsive design
- Recharts for dashboard visualizations
- Role-based UI filtering

### Infrastructure
- Docker Compose deployment with macvlan networking
- FastAPI serving React SPA (single container)
- MariaDB 10.11 with utf8mb4 encoding
- Alembic database migrations
- Automatic SSL certificate detection in entrypoint

---

*Document Version: 1.0 — March 2026*
