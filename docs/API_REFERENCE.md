# API Reference — IT Asset Manager v2.7.5

## Overview

- **Base URL:** `https://<app-ip>:<port>/api`
- **Total endpoints:** 125+
- **Authentication:** JWT Bearer Token (8-hour expiry)
- **Format:** All requests and responses in JSON
- **Interactive docs:** Swagger UI at `/docs`, ReDoc at `/redoc`

## Authentication

### Login

```
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=your-password
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Rate limited:** 5 attempts/minute. Returns `429 Too Many Requests` when exceeded.

All subsequent requests require:
```
Authorization: Bearer <access_token>
```

### Current User

```
GET /api/auth/me → { "username": "admin", "role": "admin" }
```

### Change Password

```
POST /api/auth/change-password
{ "current_password": "...", "new_password": "..." }
```

## Endpoint Summary

### Assets (`/api/assets`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List all assets (paginated, filterable) | All |
| GET | `/{id}` | Get asset details | All |
| POST | `/` | Create asset | Admin, Operator |
| PUT | `/{id}` | Update asset | Admin, Operator |
| DELETE | `/{id}` | Soft-delete asset | Admin |
| GET | `/export` | Export assets to Excel | Admin |
| PUT | `/{id}/withdraw-for-maintenance` | Set maintenance status | Admin, Operator |

### Asset Types (`/api/asset-types`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List all types (hierarchical) | All |
| GET | `/{id}` | Get type details | All |
| POST | `/` | Create type | Admin |
| PUT | `/{id}` | Update type | Admin |
| DELETE | `/{id}` | Delete type (if no linked assets) | Admin |

### People (`/api/people`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List people (filterable by site) | All |
| GET | `/{id}` | Get person with assignments | All |
| POST | `/` | Create person | Admin, Operator |
| PUT | `/{id}` | Update person | Admin, Operator |
| DELETE | `/{id}` | Soft-delete person | Admin |

### Assignments (`/api/assignments`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List assignments (filterable) | All |
| GET | `/{id}` | Get assignment with items | All |
| POST | `/` | Create assignment with items | Admin, Operator |
| PUT | `/{id}` | Update assignment | Admin, Operator |
| DELETE | `/{id}` | Delete assignment (cascades items) | Admin |
| GET | `/{id}/pdf` | Generate assignment PDF | All |
| POST | `/{id}/return` | Process full return | Admin, Operator |
| POST | `/{id}/partial-return` | Process partial return | Admin, Operator |

### SIMs (`/api/sims`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List SIMs (PIN/PUK encrypted) | All |
| GET | `/{id}` | Get SIM details (decrypted) | Admin, Operator |
| POST | `/` | Create SIM | Admin, Operator |
| PUT | `/{id}` | Update SIM | Admin, Operator |
| DELETE | `/{id}` | Soft-delete SIM | Admin |

PIN and PUK values are encrypted at rest using Fernet AES-128-CBC. They are decrypted only on individual GET requests by authorized users.

### Badges (`/api/badges`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List badges | All |
| GET | `/{id}` | Get badge details | All |
| POST | `/` | Create badge | Admin, Operator |
| PUT | `/{id}` | Update badge | Admin, Operator |
| DELETE | `/{id}` | Soft-delete badge | Admin |

### Inventory (`/api/inventory`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List inventory SKUs | All |
| GET | `/{id}` | Get SKU details | All |
| POST | `/` | Create SKU | Admin, Operator |
| PUT | `/{id}` | Update SKU (stock levels) | Admin, Operator |
| DELETE | `/{id}` | Soft-delete SKU | Admin |

### Sites (`/api/sites`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List sites | All |
| POST | `/` | Create site | Admin |
| PUT | `/{id}` | Update site | Admin |
| DELETE | `/{id}` | Delete site | Admin |

### Locations (`/api/locations`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List locations (filterable by site) | All |
| POST | `/` | Create location | Admin |
| PUT | `/{id}` | Update location | Admin |
| DELETE | `/{id}` | Delete location | Admin |

### Suppliers (`/api/suppliers`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List suppliers | All |
| POST | `/` | Create supplier | Admin |
| PUT | `/{id}` | Update supplier | Admin |
| DELETE | `/{id}` | Soft-delete supplier | Admin |

### Dashboard (`/api/dashboard`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/stats` | General statistics | All |
| GET | `/assets-by-type` | Assets grouped by type | All |
| GET | `/assets-by-status` | Assets grouped by status | All |
| GET | `/assets-by-site` | Assets grouped by site | All |
| GET | `/recent-assignments` | Recent assignment activity | All |

### Reports (`/api/reports`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/assets` | Asset report (filterable) | Admin, Operator |
| GET | `/assignments` | Assignment report | Admin, Operator |
| GET | `/inventory` | Inventory status report | Admin, Operator |
| GET | `/export/assets` | Export to Excel | Admin |

### Users (`/api/users`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List users | Admin |
| GET | `/{id}` | Get user details | Admin |
| POST | `/` | Create user | Admin |
| PUT | `/{id}` | Update user | Admin |
| PATCH | `/{id}/role` | Change user role | Admin |
| DELETE | `/{id}` | Delete user | Admin |

### Audit Logs (`/api/audit-logs`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List audit logs (paginated) | Admin |
| DELETE | `/rotate` | Rotate old logs (archival) | Admin |

Audit logs are automatically encrypted at rest. The `details` field uses Fernet encryption.

### Document Templates (`/api/document-templates`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/` | List templates | Admin |
| POST | `/` | Create template | Admin |
| PUT | `/{id}` | Update template | Admin |
| DELETE | `/{id}` | Delete template | Admin |

## GDPR Endpoints (`/api/gdpr`)

Implements EU Regulation 2016/679 data subject rights. Available to all authenticated users for their own data. Every request is automatically logged in the audit trail.

| Method | Path | Article | Description |
|--------|------|---------|-------------|
| GET | `/my-data` | Art. 15 | Export all personal data |
| GET | `/data-portability` | Art. 20 | Machine-readable data export |
| PUT | `/rectification` | Art. 16 | Correct inaccurate data |
| DELETE | `/erasure` | Art. 17 | Account anonymization (irreversible) |
| POST | `/restriction` | Art. 18 | Restrict data processing |
| POST | `/objection` | Art. 21 | Object to data processing |

**Erasure implementation:** Anonymization (not physical deletion) — username, email, and personal data are replaced with anonymized placeholders. Audit logs are preserved per ISO 27001 requirements.

## Compliance Endpoints (`/api/compliance`)

| Method | Path | Description | Roles |
|--------|------|-------------|-------|
| GET | `/results` | Latest compliance report | Admin |
| GET | `/guide` | SSH commands for running tests | Admin |
| GET | `/reports` | List available PDF reports | Admin |
| GET | `/download-report/{filename}` | Download PDF report | Admin |
| GET | `/encryption-check` | Encryption verification (3 tests) | Admin |
| GET | `/db-check` | Database connectivity check | Admin |

## Health Check

```
GET /api/health → { "status": "ok" }
```

No authentication required. Used by Docker health checks and the compliance container.

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad request (validation error) |
| 401 | Unauthorized (missing or invalid token) |
| 403 | Forbidden (insufficient role) |
| 404 | Not found |
| 409 | Conflict (duplicate entry) |
| 422 | Unprocessable entity (Pydantic validation) |
| 429 | Too many requests (rate limited) |
| 500 | Internal server error |

## Role-Based Filtering

Users with role `user` automatically see only their own data. The backend applies filters based on their linked `person_id`:

- **Assets:** only assets assigned to their person
- **Assignments:** only their own assignments
- **SIMs:** only SIMs assigned to their person
- **Badges:** only their own badges

Admin and Operator roles see all records.

---

*Document Version: 1.0 — March 2026*
