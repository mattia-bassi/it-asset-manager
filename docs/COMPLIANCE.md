# Compliance — IT Asset Manager v2.7.5

## Overview

IT Asset Manager is designed to meet **ISO 27001:2022** (Information Security Management) and **EU GDPR 2016/679** (Data Protection) requirements. Compliance is verified automatically through 26 controls executed by an independent audit container.

## Compliance Architecture

Following ISO 27001 Clause 9.2, the auditor must be independent from the auditee:

```
┌───────────────────┐         HTTP         ┌───────────────────┐
│ asset-compliance  │ ──────────────────▶  │    asset-app      │
│ (auditor)         │                      │    (auditee)      │
│                   │ ◀──────────────────  │                   │
│ 26 automated      │      Responses       │ Responds to       │
│ tests             │                      │ test requests     │
│ JSON + PDF report │                      │                   │
└───────────────────┘                      └───────────────────┘
```

The compliance container:
- Runs as a one-shot Docker container (`docker compose run --rm compliance`)
- Has no access to the database, filesystem, or Docker socket
- Communicates only via HTTP with the application
- Generates JSON and PDF reports in a shared volume
- Takes approximately 90 seconds (includes rate limit verification)

## Running Compliance Tests

```bash
cd /path/to/it-asset-manager
docker compose run --rm compliance
```

### Expected Results

| Environment | Score | Notes |
|-------------|-------|-------|
| HTTP (development) | 25/26 | HTTPS test fails (expected) |
| HTTPS (production) | 26/26 | All controls pass |

## Test Matrix (26 Controls)

### 1. HTTPS/TLS (1 test)

| # | Control | Standard | Pass Criteria |
|---|---------|----------|---------------|
| 1 | HTTPS active connection | ISO 27001 A.8.24 | APP_URL starts with `https` + status 200 |

### 2. OWASP Security Headers (6 tests)

| # | Control | Header | Expected Value |
|---|---------|--------|----------------|
| 2 | X-Content-Type-Options | `X-Content-Type-Options` | `nosniff` |
| 3 | X-Frame-Options | `X-Frame-Options` | `DENY` |
| 4 | X-XSS-Protection | `X-XSS-Protection` | `1; mode=block` |
| 5 | Referrer-Policy | `Referrer-Policy` | `strict-origin-when-cross-origin` |
| 6 | Content-Security-Policy | `Content-Security-Policy` | Present |
| 7 | Permissions-Policy | `Permissions-Policy` | Present |

### 3. Rate Limiting (1 test)

| # | Control | Standard | Pass Criteria |
|---|---------|----------|---------------|
| 8 | Rate limit triggered within 6 attempts | ISO 27001 A.8.16 | Receives HTTP 429 |

After this test, the system waits 61 seconds for the rate limit counter to reset.

### 4. Authentication (3 tests)

| # | Control | Standard | Pass Criteria |
|---|---------|----------|---------------|
| 9 | Valid admin login | ISO 27001 A.8.5 | Status 200 + `access_token` |
| 10 | Wrong password rejected | ISO 27001 A.8.5 | Status 401 |
| 11 | No-token access rejected | ISO 27001 A.8.5 | Status 401 or 403 |

### 5. GDPR Data Subject Rights (5 tests)

| # | Control | GDPR Article | Endpoint | Pass Criteria |
|---|---------|-------------|----------|---------------|
| 12 | Right of access | Art. 15 | GET `/api/gdpr/my-data` | Status 200 |
| 13 | Data portability | Art. 20 | GET `/api/gdpr/data-portability` | Status 200 |
| 14 | Right to erasure | Art. 17 | DELETE `/api/gdpr/erasure` | Status 200/422/400 |
| 15 | Right to rectification | Art. 16 | PUT `/api/gdpr/rectification` | Status 200/422/400 |
| 16 | Right to restriction | Art. 18 | POST `/api/gdpr/restriction` | Status 200/422/400 |

Tests 14-16 accept 422/400 because the test sends no request body — the important thing is that the endpoint exists and responds (not 404/500).

### 6. Audit Logging (3 tests)

| # | Control | Standard | Pass Criteria |
|---|---------|----------|---------------|
| 17 | Audit logs endpoint works | ISO 27001 A.12.4.1 | GET `/api/audit-logs` returns 200 |
| 18 | Audit logs present | ISO 27001 A.12.4.1 | `total > 0` |
| 19 | Log structure complete | ISO 27001 A.12.4.1 | Fields: id, action, entity_type, created_at |

### 7. Encryption at Rest (3 tests)

| # | Control | Standard | Pass Criteria |
|---|---------|----------|---------------|
| 20 | Encrypt produces Fernet token | ISO 27001 A.8.24 | Valid Fernet token returned |
| 21 | Decrypt returns plaintext | ISO 27001 A.8.24 | Original string recovered |
| 22 | Backward compat: plaintext pass-through | ISO 27001 A.8.24 | Unencrypted string returned unchanged |

Tested via `/api/compliance/encryption-check` endpoint.

### 8. Log Rotation (3 tests)

| # | Control | Standard | Pass Criteria |
|---|---------|----------|---------------|
| 23 | Log rotation endpoint works | ISO 27001 A.12.4.1 | DELETE `/api/audit-logs/rotate` returns 200 |
| 24 | Response includes archived_count | ISO 27001 A.12.4.1 | Field present |
| 25 | Response includes remaining_count | ISO 27001 A.12.4.1 | Field present |

### 9. Database Hardening (1 test)

| # | Control | Standard | Pass Criteria |
|---|---------|----------|---------------|
| 26 | Database connection working | ISO 27001 A.8.20 | GET `/api/compliance/db-check` returns 200 |

## GDPR Implementation

### Data Subject Rights (Art. 15-21)

| Article | Right | Implementation |
|---------|-------|----------------|
| Art. 15 | Right of access | Full data export (JSON) via `/api/gdpr/my-data` |
| Art. 16 | Right to rectification | Update personal data via `/api/gdpr/rectification` |
| Art. 17 | Right to erasure | Anonymization (not deletion) via `/api/gdpr/erasure` |
| Art. 18 | Right to restriction | Restrict processing via `/api/gdpr/restriction` |
| Art. 20 | Right to portability | Machine-readable export via `/api/gdpr/data-portability` |
| Art. 21 | Right to object | Object to processing via `/api/gdpr/objection` |

### Erasure Implementation (Art. 17)

The system implements anonymization rather than physical deletion:
- Username → `deleted_user_{id}`
- Email → `deleted_{id}@anonymized.local`
- Account is deactivated
- Audit logs are preserved (ISO 27001 requirement for traceability)

### Privacy by Design (Art. 25)

- Encryption at rest for sensitive data (SIM PIN/PUK, audit log details)
- Role-based access control with minimum privilege
- Automatic audit logging on every CRUD operation
- Log rotation to limit data retention

### Record of Processing (Art. 30)

Every data processing operation is automatically recorded in the audit log with:
- User ID and username of the operator
- Action performed (CREATE, UPDATE, DELETE, etc.)
- Entity type and entity ID affected
- Timestamp
- IP address

## ISO 27001:2022 Controls

### Implemented Controls

| Control | Description | Implementation |
|---------|-------------|----------------|
| A.5.1 | Information security policies | Documented in compliance reports |
| A.8.5 | Secure authentication | JWT + Argon2id + rate limiting |
| A.8.9 | Configuration management | OWASP security headers |
| A.8.16 | Monitoring activities | Rate limiting on login endpoint |
| A.8.20 | Network security | macvlan isolation, DB access restricted |
| A.8.24 | Use of cryptography | Fernet AES-128-CBC, HTTPS/TLS |
| A.9.2 | Internal audit | Independent compliance container |
| A.12.4.1 | Event logging | Encrypted audit log with rotation |

### Security Hardening

| Measure | Details |
|---------|---------|
| Password hashing | Argon2id (OWASP recommended) |
| Password policy | Minimum 12 characters |
| JWT expiry | 8 hours |
| Rate limiting | 5 login attempts/minute (Redis-backed) |
| SQL injection | SQLAlchemy ORM for all data operations; `text()` used only for health check queries (`SELECT 1`) — no raw queries with user-supplied input. |
| XSS protection | Content-Security-Policy + X-XSS-Protection |
| Clickjacking | X-Frame-Options: DENY |
| CORS | Configurable allowed origins |
| Database access | Application user only from app container IP |

## Compliance Reports

### Viewing Results

- **Web UI:** Settings → Compliance → click "Refresh Results"
- **Disk:** Reports saved in `data/compliance/`
  - `latest_report.json` — consumed by the application UI
  - `compliance_report_YYYYMMDD_HHMMSS.pdf` — for audit documentation

### PDF Report Contents

Each PDF report includes:
- Execution date and operator
- System version
- Score summary (passed/total)
- Detailed results per category
- Signature section for IT Manager and Management approval

---

*Document Version: 1.0 — March 2026*
