# Database Schema — IT Asset Manager v2.7.5

## Overview

- **Engine:** MariaDB 10.11
- **Database:** configurable (default: `assetdb`)
- **Tables:** 17
- **Foreign keys:** 21
- **Encoding:** utf8mb4 / utf8mb4_unicode_ci
- **Migration tool:** Alembic (head: `0001_initial_v274`)

## Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐
│    users    │────1:1──▶│   people    │
└─────────────┘         └─────────────┘
                               │
                          site_id (FK)
                               ▼
                        ┌─────────────┐
                        │    sites    │
                        └─────────────┘
                               │
                          site_id (FK)
                               ▼
┌──────────────────┐    ┌─────────────┐
│ location_types   │◀───│  locations  │
└──────────────────┘    └─────────────┘
                               │
                         location_id (FK)
                               ▼
┌─────────────┐         ┌──────────────┐
│ asset_types │◀────────│    assets    │
└─────────────┘         └──────────────┘
                               │
                          asset_id (FK)
                               ▼
┌─────────────┐         ┌──────────────────┐
│ assignments │◀────────│ assignment_items  │
└─────────────┘         └──────────────────┘
                            │  │  │  │
                            ▼  ▼  ▼  ▼
                      assets  inventory  sims  badges
                               _skus

┌─────────────┐    ┌──────────────┐    ┌───────────────────┐
│  suppliers  │    │  audit_logs  │    │ document_templates│
└─────────────┘    └──────────────┘    └───────────────────┘
```

## Tables

### users

Authentication and authorization accounts.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| username | VARCHAR(50) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL |
| role | ENUM('admin','operator','user') | NOT NULL, DEFAULT 'user' |
| person_id | INT | FK → people.id, NULLABLE |
| is_active | TINYINT(1) | DEFAULT 1 |
| is_permanently_disabled | TINYINT(1) | DEFAULT 0 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### people

Employee directory linked to sites.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| first_name | VARCHAR(100) | NOT NULL |
| last_name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(100) | UNIQUE, NOT NULL |
| site_id | INT | FK → sites.id, NULLABLE |
| extension | VARCHAR(20) | NULLABLE |
| mobile_phone | VARCHAR(20) | NULLABLE |
| notes | TEXT | NULLABLE |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### sites

Company locations/offices.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| name | VARCHAR(100) | NOT NULL |
| address | VARCHAR(200) | NULLABLE |
| city | VARCHAR(100) | NULLABLE |
| province | VARCHAR(50) | NULLABLE |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### assets

IT devices and equipment.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| asset_type_id | INT | FK → asset_types.id, NOT NULL |
| brand | VARCHAR(100) | NULLABLE |
| model | VARCHAR(100) | NULLABLE |
| serial_number | VARCHAR(100) | UNIQUE, NULLABLE |
| internal_code | VARCHAR(100) | UNIQUE, NULLABLE |
| status | VARCHAR(50) | DEFAULT 'available' |
| site_id | INT | FK → sites.id, NULLABLE |
| person_id | INT | FK → people.id, NULLABLE |
| location_id | INT | FK → locations.id, NULLABLE |
| purchase_date | DATE | NULLABLE |
| warranty_expiry | DATE | NULLABLE |
| notes | TEXT | NULLABLE |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### asset_types

Hierarchical asset categories (supports parent-child via `parent_id`).

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| name | VARCHAR(100) | NOT NULL |
| parent_id | INT | FK → asset_types.id, NULLABLE |
| fields_schema | JSON | NULLABLE (custom field definitions) |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### assignments

Material assignments to people or locations.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| person_id | INT | FK → people.id, NULLABLE |
| location_id | INT | FK → locations.id, NULLABLE |
| status | VARCHAR(50) | DEFAULT 'active' |
| assignment_date | DATE | NOT NULL |
| return_date | DATE | NULLABLE |
| document_path | VARCHAR(500) | NULLABLE |
| created_by | INT | NULLABLE |
| notes | TEXT | NULLABLE |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

Business rule: either `person_id` or `location_id` must be set, not both.

### assignment_items

Individual items within an assignment. Supports polymorphic references.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| assignment_id | INT | FK → assignments.id, NOT NULL, CASCADE |
| item_type | VARCHAR(20) | NOT NULL ('asset','inventory','sim','badge') |
| asset_id | INT | FK → assets.id, NULLABLE |
| inventory_sku_id | INT | FK → inventory_skus.id, NULLABLE |
| sim_id | INT | FK → sims.id, NULLABLE |
| badge_id | INT | FK → badges.id, NULLABLE |
| quantity | INT | DEFAULT 1 |
| notes | TEXT | NULLABLE |

Business rule: exactly one of `asset_id`, `inventory_sku_id`, `sim_id`, `badge_id` must be set, matching `item_type`.

### inventory_skus

Consumable materials and supplies.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| category | VARCHAR(100) | NOT NULL |
| device | VARCHAR(200) | NOT NULL |
| brand | VARCHAR(100) | NULLABLE |
| site_id | INT | FK → sites.id, NULLABLE |
| quantity | INT | DEFAULT 0 |
| min_quantity | INT | DEFAULT 5 (reorder threshold) |
| notes | TEXT | NULLABLE |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### sims

Corporate SIM cards with encrypted PIN/PUK.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| seriale | VARCHAR(100) | UNIQUE, NOT NULL |
| operatore | VARCHAR(50) | NOT NULL |
| numero | VARCHAR(20) | NULLABLE |
| pin | VARCHAR(255) | NULLABLE (Fernet encrypted) |
| puk | VARCHAR(255) | NULLABLE (Fernet encrypted) |
| status | VARCHAR(50) | DEFAULT 'attiva' |
| person_id | INT | FK → people.id, NULLABLE |
| site_id | INT | FK → sites.id, NULLABLE |
| notes | TEXT | NULLABLE |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### badges

Employee identification badges.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| numero_badge | VARCHAR(50) | UNIQUE, NOT NULL |
| tipo | VARCHAR(50) | DEFAULT 'dipendente' |
| status | VARCHAR(50) | DEFAULT 'attivo' |
| data_emissione | DATE | NOT NULL |
| data_scadenza | DATE | NULLABLE |
| site_id | INT | FK → sites.id, NULLABLE |
| person_id | INT | FK → people.id, NULLABLE |
| notes | VARCHAR(500) | NULLABLE |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### locations

Physical rooms/spaces within a site.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| name | VARCHAR(200) | NOT NULL |
| site_id | INT | FK → sites.id, NOT NULL, CASCADE |
| location_type_id | INT | FK → location_types.id, NULLABLE |
| floor | VARCHAR(20) | NULLABLE |
| notes | TEXT | NULLABLE |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### location_types

Classification for locations (e.g., Server Room, Meeting Room).

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| name | VARCHAR(100) | UNIQUE, NOT NULL |
| description | TEXT | NULLABLE |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### suppliers

Vendor and supplier registry.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| name | VARCHAR(200) | NOT NULL |
| contact_name | VARCHAR(100) | NULLABLE |
| email | VARCHAR(100) | NULLABLE |
| phone | VARCHAR(50) | NULLABLE |
| address | TEXT | NULLABLE |
| notes | TEXT | NULLABLE |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### audit_logs

Compliance audit trail. Details field is encrypted at rest.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| user_id | INT | FK → users.id, NULLABLE |
| username | VARCHAR(50) | NULLABLE |
| action | VARCHAR(100) | NOT NULL |
| entity_type | VARCHAR(50) | NULLABLE |
| entity_id | INT | NULLABLE |
| details | TEXT | NULLABLE (Fernet encrypted) |
| old_value | TEXT | NULLABLE |
| new_value | TEXT | NULLABLE |
| ip_address | VARCHAR(45) | NULLABLE |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

### document_templates

Templates for PDF document generation.

| Column | Type | Constraints |
|--------|------|-------------|
| id | INT | PK, AUTO_INCREMENT |
| name | VARCHAR(100) | NOT NULL |
| description | TEXT | NULLABLE |
| logo_path | VARCHAR(500) | NULLABLE |
| footer_path | VARCHAR(500) | NULLABLE |
| is_default | TINYINT(1) | DEFAULT 0 |
| is_active | TINYINT(1) | DEFAULT 1 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | ON UPDATE CURRENT_TIMESTAMP |

### alembic_version

Alembic migration tracking (auto-managed).

| Column | Type | Constraints |
|--------|------|-------------|
| version_num | VARCHAR(32) | PK, NOT NULL |

## Foreign Key Summary

| Table | Column | References | On Delete |
|-------|--------|------------|-----------|
| users | person_id | people.id | SET NULL |
| people | site_id | sites.id | SET NULL |
| assets | asset_type_id | asset_types.id | RESTRICT |
| assets | site_id | sites.id | SET NULL |
| assets | person_id | people.id | SET NULL |
| assets | location_id | locations.id | SET NULL |
| assignments | person_id | people.id | CASCADE |
| assignments | location_id | locations.id | SET NULL |
| assignment_items | assignment_id | assignments.id | CASCADE |
| assignment_items | asset_id | assets.id | SET NULL |
| assignment_items | inventory_sku_id | inventory_skus.id | SET NULL |
| assignment_items | sim_id | sims.id | SET NULL |
| assignment_items | badge_id | badges.id | SET NULL |
| sims | person_id | people.id | SET NULL |
| sims | site_id | sites.id | SET NULL |
| badges | person_id | people.id | SET NULL |
| badges | site_id | sites.id | SET NULL |
| audit_logs | user_id | users.id | SET NULL |
| inventory_skus | site_id | sites.id | SET NULL |
| locations | site_id | sites.id | CASCADE |
| locations | location_type_id | location_types.id | SET NULL |

## Delete Behavior

- **CASCADE:** Deleting an `assignment` removes all its `assignment_items`. Deleting a `site` removes its `locations`.
- **SET NULL:** Deleting a `person` nullifies references in `users`, `assets`, `sims`, `badges`.
- **RESTRICT:** Cannot delete an `asset_type` if assets reference it.

---

*Document Version: 1.0 — March 2026*
