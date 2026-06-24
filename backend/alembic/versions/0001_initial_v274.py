"""Initial schema from production v2.7.4

Revision ID: 0001_initial_v274
Revises: 
Create Date: 2026-03-24

Generated from mysqldump of production QNAP database.
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_v274"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. sites (no FK dependencies)
    op.execute("""
        CREATE TABLE `sites` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `name` varchar(200) DEFAULT NULL,
            `address` text DEFAULT NULL,
            `notes` text DEFAULT NULL,
            `created_at` datetime NOT NULL DEFAULT current_timestamp(),
            `city` varchar(100) DEFAULT NULL,
            `postal_code` varchar(20) DEFAULT NULL,
            `country` varchar(100) DEFAULT NULL,
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            `centralino` varchar(50) DEFAULT NULL,
            PRIMARY KEY (`id`),
            UNIQUE KEY `name` (`name`),
            KEY `idx_sites_name` (`name`),
            KEY `idx_sites_is_active` (`is_active`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 2. suppliers (no FK dependencies)
    op.execute("""
        CREATE TABLE `suppliers` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `name` varchar(150) NOT NULL,
            `contact_person` varchar(100) DEFAULT NULL,
            `phone` varchar(50) DEFAULT NULL,
            `email` varchar(150) DEFAULT NULL,
            `website` varchar(200) DEFAULT NULL,
            `contract_number` varchar(100) DEFAULT NULL,
            `warranty_conditions` text DEFAULT NULL,
            `warranty_duration_months` int(11) DEFAULT NULL,
            `notes` text DEFAULT NULL,
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `created_at` datetime DEFAULT current_timestamp(),
            PRIMARY KEY (`id`),
            KEY `idx_suppliers_name` (`name`),
            KEY `idx_suppliers_is_active` (`is_active`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 3. location_types (no FK dependencies)
    op.execute("""
        CREATE TABLE `location_types` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `name` varchar(100) NOT NULL,
            `icon` varchar(50) DEFAULT NULL,
            `description` text DEFAULT NULL,
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            PRIMARY KEY (`id`),
            UNIQUE KEY `idx_location_types_name` (`name`),
            KEY `idx_location_types_is_active` (`is_active`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 4. asset_types (self-referencing FK)
    op.execute("""
        CREATE TABLE `asset_types` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `name` varchar(100) NOT NULL,
            `parent_id` int(11) DEFAULT NULL,
            `description` text DEFAULT NULL,
            `fields_schema` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`fields_schema`)),
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            PRIMARY KEY (`id`),
            KEY `idx_asset_types_parent_id` (`parent_id`),
            CONSTRAINT `asset_types_ibfk_1` FOREIGN KEY (`parent_id`) REFERENCES `asset_types` (`id`) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 5. document_templates (no FK dependencies)
    op.execute("""
        CREATE TABLE `document_templates` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `name` varchar(100) NOT NULL,
            `description` text DEFAULT NULL,
            `logo_path` varchar(500) DEFAULT NULL,
            `footer_path` varchar(500) DEFAULT NULL,
            `is_default` tinyint(1) NOT NULL DEFAULT 0,
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            PRIMARY KEY (`id`),
            KEY `idx_document_templates_name` (`name`),
            KEY `idx_document_templates_is_active` (`is_active`),
            KEY `idx_document_templates_is_default` (`is_default`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 6. people (FK -> sites)
    op.execute("""
        CREATE TABLE `people` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `first_name` varchar(100) NOT NULL,
            `last_name` varchar(100) NOT NULL,
            `site_id` int(11) DEFAULT NULL,
            `email` varchar(255) DEFAULT NULL,
            `extension` varchar(20) DEFAULT NULL,
            `mobile_phone` varchar(50) DEFAULT NULL,
            `notes` text DEFAULT NULL,
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            PRIMARY KEY (`id`),
            UNIQUE KEY `email` (`email`),
            KEY `idx_people_last_name` (`last_name`),
            KEY `idx_people_first_name` (`first_name`),
            KEY `idx_people_site_id` (`site_id`),
            KEY `idx_people_is_active` (`is_active`),
            CONSTRAINT `people_ibfk_1` FOREIGN KEY (`site_id`) REFERENCES `sites` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 7. users (FK -> people)
    op.execute("""
        CREATE TABLE `users` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `username` varchar(64) NOT NULL,
            `password_hash` varchar(255) NOT NULL,
            `role` varchar(32) NOT NULL DEFAULT 'admin',
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `created_at` datetime NOT NULL DEFAULT current_timestamp(),
            `person_id` int(11) DEFAULT NULL,
            `is_permanently_disabled` tinyint(1) NOT NULL DEFAULT 0,
            PRIMARY KEY (`id`),
            UNIQUE KEY `username` (`username`),
            KEY `fk_users_person_id` (`person_id`),
            CONSTRAINT `fk_users_person_id` FOREIGN KEY (`person_id`) REFERENCES `people` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 8. locations (FK -> location_types, sites)
    op.execute("""
        CREATE TABLE `locations` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `name` varchar(100) NOT NULL,
            `location_type_id` int(11) DEFAULT NULL,
            `site_id` int(11) NOT NULL,
            `floor` varchar(20) DEFAULT NULL,
            `room_number` varchar(20) DEFAULT NULL,
            `notes` text DEFAULT NULL,
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            PRIMARY KEY (`id`),
            UNIQUE KEY `uq_locations_name_type_site` (`name`,`location_type_id`,`site_id`),
            KEY `idx_locations_location_type_id` (`location_type_id`),
            KEY `idx_locations_site_id` (`site_id`),
            KEY `idx_locations_is_active` (`is_active`),
            CONSTRAINT `fk_locations_location_type_id` FOREIGN KEY (`location_type_id`) REFERENCES `location_types` (`id`),
            CONSTRAINT `fk_locations_site_id` FOREIGN KEY (`site_id`) REFERENCES `sites` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 9. assets (FK -> asset_types, sites, people, locations, suppliers)
    op.execute("""
        CREATE TABLE `assets` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `asset_code` varchar(50) DEFAULT NULL,
            `serial_number` varchar(100) NOT NULL,
            `mac_address` varchar(17) DEFAULT NULL,
            `asset_type_id` int(11) NOT NULL,
            `manufacturer` varchar(100) NOT NULL,
            `model` varchar(100) NOT NULL,
            `site_id` int(11) DEFAULT NULL,
            `person_id` int(11) DEFAULT NULL,
            `status` varchar(50) NOT NULL DEFAULT 'disponibile',
            `purchase_date` date DEFAULT NULL,
            `warranty_expiry` date DEFAULT NULL,
            `specifications` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`specifications`)),
            `notes` text DEFAULT NULL,
            `qr_code` varchar(255) DEFAULT NULL,
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            `location_id` int(11) DEFAULT NULL,
            `supplier_id` int(11) DEFAULT NULL,
            PRIMARY KEY (`id`),
            UNIQUE KEY `asset_code` (`asset_code`),
            KEY `idx_assets_serial_number` (`serial_number`),
            KEY `idx_assets_mac_address` (`mac_address`),
            KEY `idx_assets_asset_type_id` (`asset_type_id`),
            KEY `idx_assets_manufacturer` (`manufacturer`),
            KEY `idx_assets_model` (`model`),
            KEY `idx_assets_site_id` (`site_id`),
            KEY `idx_assets_person_id` (`person_id`),
            KEY `idx_assets_status` (`status`),
            KEY `idx_assets_is_active` (`is_active`),
            KEY `idx_assets_status_active` (`status`,`is_active`),
            KEY `idx_assets_location_id` (`location_id`),
            KEY `idx_assets_supplier_id` (`supplier_id`),
            CONSTRAINT `assets_ibfk_1` FOREIGN KEY (`asset_type_id`) REFERENCES `asset_types` (`id`),
            CONSTRAINT `assets_ibfk_2` FOREIGN KEY (`site_id`) REFERENCES `sites` (`id`) ON DELETE SET NULL,
            CONSTRAINT `assets_ibfk_3` FOREIGN KEY (`person_id`) REFERENCES `people` (`id`) ON DELETE SET NULL,
            CONSTRAINT `fk_assets_location_id` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`) ON DELETE SET NULL,
            CONSTRAINT `fk_assets_supplier_id` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 10. inventory_skus (FK -> sites)
    op.execute("""
        CREATE TABLE `inventory_skus` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `category` varchar(100) NOT NULL,
            `device` varchar(200) NOT NULL,
            `brand` varchar(100) DEFAULT NULL,
            `site_id` int(11) DEFAULT NULL,
            `quantity` int(11) NOT NULL DEFAULT 0,
            `min_quantity` int(11) NOT NULL DEFAULT 5,
            `notes` text DEFAULT NULL,
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            PRIMARY KEY (`id`),
            KEY `idx_inventory_skus_category` (`category`),
            KEY `idx_inventory_skus_device` (`device`),
            KEY `idx_inventory_skus_brand` (`brand`),
            KEY `idx_inventory_skus_is_active` (`is_active`),
            KEY `idx_inventory_skus_site_id` (`site_id`),
            CONSTRAINT `fk_inventory_skus_site` FOREIGN KEY (`site_id`) REFERENCES `sites` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 11. sims (FK -> people, sites)
    op.execute("""
        CREATE TABLE `sims` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `seriale` varchar(100) NOT NULL,
            `operatore` varchar(50) NOT NULL,
            `site_id` int(11) DEFAULT NULL,
            `numero_telefono` varchar(20) NOT NULL,
            `pin_criptato` varchar(255) NOT NULL,
            `puk_criptato` varchar(255) NOT NULL,
            `status` enum('disponibile','assegnata','disattivata') NOT NULL,
            `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `person_id` int(11) DEFAULT NULL,
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            PRIMARY KEY (`id`),
            UNIQUE KEY `numero_telefono` (`numero_telefono`),
            UNIQUE KEY `ix_sims_seriale` (`seriale`),
            KEY `ix_sims_person_id` (`person_id`),
            KEY `ix_sims_is_active` (`is_active`),
            KEY `idx_sims_site_id` (`site_id`),
            CONSTRAINT `fk_sims_person_id` FOREIGN KEY (`person_id`) REFERENCES `people` (`id`) ON DELETE SET NULL,
            CONSTRAINT `fk_sims_site` FOREIGN KEY (`site_id`) REFERENCES `sites` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 12. badges (FK -> sites, people)
    op.execute("""
        CREATE TABLE `badges` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `numero_badge` varchar(50) NOT NULL,
            `tipo` enum('dipendente','visitatore','temporaneo') NOT NULL,
            `status` enum('attivo','disattivo','smarrito') NOT NULL,
            `data_emissione` date NOT NULL,
            `data_scadenza` date DEFAULT NULL,
            `site_id` int(11) DEFAULT NULL,
            `person_id` int(11) DEFAULT NULL,
            `notes` varchar(500) DEFAULT NULL,
            `is_active` tinyint(1) NOT NULL,
            `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            PRIMARY KEY (`id`),
            UNIQUE KEY `ix_badges_numero_badge` (`numero_badge`),
            KEY `ix_badges_id` (`id`),
            KEY `ix_badges_site_id` (`site_id`),
            KEY `ix_badges_person_id` (`person_id`),
            KEY `ix_badges_is_active` (`is_active`),
            CONSTRAINT `badges_ibfk_1` FOREIGN KEY (`site_id`) REFERENCES `sites` (`id`) ON DELETE SET NULL,
            CONSTRAINT `badges_ibfk_2` FOREIGN KEY (`person_id`) REFERENCES `people` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 13. assignments (FK -> people, users, locations)
    op.execute("""
        CREATE TABLE `assignments` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `person_id` int(11) DEFAULT NULL,
            `assignment_date` date NOT NULL,
            `return_date` date DEFAULT NULL,
            `assignment_type` varchar(50) NOT NULL,
            `status` varchar(50) NOT NULL DEFAULT 'attivo',
            `notes` text DEFAULT NULL,
            `document_path` varchar(500) DEFAULT NULL,
            `created_by` int(11) DEFAULT NULL,
            `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
            `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
            `location_id` int(11) DEFAULT NULL,
            PRIMARY KEY (`id`),
            KEY `created_by` (`created_by`),
            KEY `idx_assignments_person_id` (`person_id`),
            KEY `idx_assignments_status` (`status`),
            KEY `idx_assignments_assignment_date` (`assignment_date`),
            KEY `idx_assignments_return_date` (`return_date`),
            KEY `idx_assignments_person_status` (`person_id`,`status`),
            KEY `ix_assignments_location_id` (`location_id`),
            CONSTRAINT `assignments_ibfk_1` FOREIGN KEY (`person_id`) REFERENCES `people` (`id`),
            CONSTRAINT `assignments_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
            CONSTRAINT `fk_assignments_location_id` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 14. assignment_items (FK -> assignments, assets, inventory_skus, badges, sims)
    op.execute("""
        CREATE TABLE `assignment_items` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `assignment_id` int(11) NOT NULL,
            `item_type` varchar(20) NOT NULL,
            `asset_id` int(11) DEFAULT NULL,
            `inventory_sku_id` int(11) DEFAULT NULL,
            `sim_id` int(11) DEFAULT NULL,
            `quantity` int(11) NOT NULL DEFAULT 1,
            `notes` text DEFAULT NULL,
            `is_returned` tinyint(1) NOT NULL DEFAULT 0,
            `badge_id` int(11) DEFAULT NULL,
            PRIMARY KEY (`id`),
            KEY `idx_assignment_items_assignment_id` (`assignment_id`),
            KEY `idx_assignment_items_item_type` (`item_type`),
            KEY `idx_assignment_items_asset_id` (`asset_id`),
            KEY `idx_assignment_items_inventory_sku_id` (`inventory_sku_id`),
            KEY `idx_assignment_items_assign_type` (`assignment_id`,`item_type`),
            KEY `ix_assignment_items_is_returned` (`is_returned`),
            KEY `idx_assignment_items_sim_id` (`sim_id`),
            KEY `ix_assignment_items_badge_id` (`badge_id`),
            CONSTRAINT `assignment_items_ibfk_1` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`) ON DELETE CASCADE,
            CONSTRAINT `assignment_items_ibfk_2` FOREIGN KEY (`asset_id`) REFERENCES `assets` (`id`),
            CONSTRAINT `assignment_items_ibfk_3` FOREIGN KEY (`inventory_sku_id`) REFERENCES `inventory_skus` (`id`),
            CONSTRAINT `fk_assignment_items_badge` FOREIGN KEY (`badge_id`) REFERENCES `badges` (`id`) ON DELETE SET NULL,
            CONSTRAINT `fk_assignment_items_sim` FOREIGN KEY (`sim_id`) REFERENCES `sims` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 15. audit_logs (FK -> users)
    op.execute("""
        CREATE TABLE `audit_logs` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `user_id` int(11) DEFAULT NULL,
            `username` varchar(100) DEFAULT NULL,
            `action` varchar(100) NOT NULL,
            `entity_type` varchar(50) NOT NULL,
            `entity_id` int(11) DEFAULT NULL,
            `details` text DEFAULT NULL,
            `old_value` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`old_value`)),
            `new_value` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`new_value`)),
            `ip_address` varchar(500) DEFAULT NULL,
            `user_agent` text DEFAULT NULL,
            `created_at` datetime NOT NULL DEFAULT current_timestamp(),
            PRIMARY KEY (`id`),
            KEY `ix_audit_logs_action` (`action`),
            KEY `ix_audit_logs_created_at` (`created_at`),
            KEY `ix_audit_logs_entity_id` (`entity_id`),
            KEY `ix_audit_logs_entity_type` (`entity_type`),
            KEY `ix_audit_logs_id` (`id`),
            KEY `ix_audit_logs_user_id` (`user_id`),
            CONSTRAINT `audit_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)

    # 16. documents (FK -> users)
    op.execute("""
        CREATE TABLE `documents` (
            `id` int(11) NOT NULL AUTO_INCREMENT,
            `name` varchar(200) NOT NULL,
            `description` text DEFAULT NULL,
            `category` varchar(100) NOT NULL,
            `filename` varchar(255) NOT NULL,
            `file_path` varchar(500) NOT NULL,
            `file_size` int(11) NOT NULL,
            `mime_type` varchar(100) NOT NULL,
            `uploaded_by` int(11) DEFAULT NULL,
            `is_active` tinyint(1) NOT NULL DEFAULT 1,
            `created_at` datetime NOT NULL DEFAULT current_timestamp(),
            PRIMARY KEY (`id`),
            KEY `idx_documents_category` (`category`),
            KEY `idx_documents_uploaded_by` (`uploaded_by`),
            KEY `idx_documents_is_active` (`is_active`),
            CONSTRAINT `documents_ibfk_1` FOREIGN KEY (`uploaded_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS `documents`")
    op.execute("DROP TABLE IF EXISTS `audit_logs`")
    op.execute("DROP TABLE IF EXISTS `assignment_items`")
    op.execute("DROP TABLE IF EXISTS `assignments`")
    op.execute("DROP TABLE IF EXISTS `badges`")
    op.execute("DROP TABLE IF EXISTS `sims`")
    op.execute("DROP TABLE IF EXISTS `inventory_skus`")
    op.execute("DROP TABLE IF EXISTS `assets`")
    op.execute("DROP TABLE IF EXISTS `locations`")
    op.execute("DROP TABLE IF EXISTS `users`")
    op.execute("DROP TABLE IF EXISTS `people`")
    op.execute("DROP TABLE IF EXISTS `document_templates`")
    op.execute("DROP TABLE IF EXISTS `asset_types`")
    op.execute("DROP TABLE IF EXISTS `location_types`")
    op.execute("DROP TABLE IF EXISTS `suppliers`")
    op.execute("DROP TABLE IF EXISTS `sites`")
