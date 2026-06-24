from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, delete
from fastapi import Request
import json
import logging
import os
from datetime import datetime, timedelta

from app.models.audit_log import AuditLog
from app.core.log_encryption import encrypt_log, decrypt_log

logger = logging.getLogger(__name__)

# Campi sensibili da criptare/decriptare
ENCRYPTED_FIELDS = ["details", "ip_address", "old_value", "new_value"]


def _decrypt_audit_log(log: AuditLog) -> AuditLog:
    """
    Decripta i campi sensibili di un AuditLog in-place.
    Backward compatible: dati non criptati restituiti invariati.
    """
    for field in ENCRYPTED_FIELDS:
        value = getattr(log, field, None)
        if value:
            setattr(log, field, decrypt_log(value))
    return log


class AuditService:
    """
    Service per gestire l'audit logging completo.
    Implementa ISO 27001:2022 A.12.4.1 - Event logging.
    Implementa ISO 27001:2022 A.8.24 - Log encryption at rest.
    """

    @staticmethod
    def log_action(
        db: Session,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        details: Optional[str] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request: Optional[Request] = None
    ) -> Optional[AuditLog]:
        """
        Crea un nuovo record di audit log con encryption dei campi sensibili.

        I campi details, ip_address, old_value, new_value vengono criptati
        con Fernet prima del salvataggio nel database.

        Args:
            db: SQLAlchemy session
            action: Azione eseguita (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, etc.)
            entity_type: Tipo di entità (asset, person, user, etc.)
            entity_id: ID dell'entità (opzionale)
            details: Dettagli aggiuntivi in formato testo
            user_id: ID dell'utente che ha eseguito l'azione
            username: Username dell'utente
            old_value: Valore precedente (dict, verrà serializzato in JSON)
            new_value: Nuovo valore (dict, verrà serializzato in JSON)
            ip_address: IP address del client
            user_agent: User agent del browser
            request: FastAPI Request object (per estrarre IP e user agent automaticamente)

        Returns:
            AuditLog object se creato con successo, None se fallisce
        """
        try:
            # Estrai IP e user agent dalla Request se fornita
            if request:
                if not ip_address:
                    ip_address = request.client.host if request.client else None
                if not user_agent:
                    user_agent = request.headers.get("user-agent")

            # Serializza old_value e new_value in JSON se sono dict
            old_value_json = None
            new_value_json = None

            if old_value is not None:
                old_value_json = json.dumps(old_value, ensure_ascii=False, default=str)

            if new_value is not None:
                new_value_json = json.dumps(new_value, ensure_ascii=False, default=str)

            # --- ENCRYPTION AT REST (ISO 27001 A.8.24) ---
            encrypted_details = encrypt_log(details) if details else details
            encrypted_ip = encrypt_log(ip_address) if ip_address else ip_address
            encrypted_old = encrypt_log(old_value_json) if old_value_json else old_value_json
            encrypted_new = encrypt_log(new_value_json) if new_value_json else new_value_json

            # Crea il record di audit log con campi criptati
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=encrypted_details,
                username=username,
                old_value=encrypted_old,
                new_value=encrypted_new,
                ip_address=encrypted_ip,
                user_agent=user_agent
            )

            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)

            return audit_log

        except Exception as e:
            # Non bloccare l'operazione principale se il logging fallisce
            db.rollback()
            logger.error("Errore durante il logging dell'audit: %s", str(e))
            return None

    @staticmethod
    def get_logs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None
    ) -> tuple[list[AuditLog], int]:
        """
        Recupera i log di audit con filtri e paginazione.
        I campi sensibili vengono decriptati automaticamente.

        Args:
            db: SQLAlchemy session
            skip: Numero di record da saltare (paginazione)
            limit: Numero massimo di record da restituire
            action: Filtra per azione specifica
            entity_type: Filtra per tipo di entità
            entity_id: Filtra per ID entità specifico
            user_id: Filtra per ID utente
            username: Filtra per username (ricerca parziale)
            date_from: Data inizio range
            date_to: Data fine range
            search: Ricerca testuale in details, username, action

        Returns:
            Tupla (lista di AuditLog, totale record)
        """
        # Query base
        query = select(AuditLog)
        count_query = select(func.count()).select_from(AuditLog)

        # Filtri
        filters = []

        if action:
            filters.append(AuditLog.action == action)

        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)

        if entity_id is not None:
            filters.append(AuditLog.entity_id == entity_id)

        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)

        if username:
            filters.append(AuditLog.username.ilike(f"%{username}%"))

        if date_from:
            filters.append(AuditLog.created_at >= date_from)

        if date_to:
            filters.append(AuditLog.created_at <= date_to)

        if search:
            search_pattern = f"%{search}%"
            filters.append(
                or_(
                    AuditLog.details.ilike(search_pattern),
                    AuditLog.username.ilike(search_pattern),
                    AuditLog.action.ilike(search_pattern)
                )
            )

        # Applica filtri
        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Ordina per data decrescente (più recenti prima)
        query = query.order_by(AuditLog.created_at.desc())

        # Conta totale
        total = db.execute(count_query).scalar()

        # Paginazione
        query = query.offset(skip).limit(limit)

        # Esegui query
        results = db.execute(query).scalars().all()

        # --- DECRYPT AT READ (transparent decryption) ---
        decrypted_results = [_decrypt_audit_log(log) for log in results]

        return (decrypted_results, total)

    @staticmethod
    def get_entity_history(
        db: Session,
        entity_type: str,
        entity_id: int,
        limit: int = 50
    ) -> list[AuditLog]:
        """
        Recupera la storia completa di un'entità specifica.
        I campi sensibili vengono decriptati automaticamente.

        Args:
            db: SQLAlchemy session
            entity_type: Tipo di entità (asset, person, etc.)
            entity_id: ID dell'entità
            limit: Numero massimo di record (default 50)

        Returns:
            Lista di AuditLog ordinati per data decrescente
        """
        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.entity_type == entity_type,
                    AuditLog.entity_id == entity_id
                )
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        results = db.execute(query).scalars().all()

        # --- DECRYPT AT READ ---
        return [_decrypt_audit_log(log) for log in results]

    @staticmethod
    def get_user_activity(
        db: Session,
        user_id: int,
        limit: int = 100
    ) -> list[AuditLog]:
        """
        Recupera l'attività recente di un utente specifico.
        I campi sensibili vengono decriptati automaticamente.

        Args:
            db: SQLAlchemy session
            user_id: ID dell'utente
            limit: Numero massimo di record (default 100)

        Returns:
            Lista di AuditLog ordinati per data decrescente
        """
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )

        results = db.execute(query).scalars().all()

        # --- DECRYPT AT READ ---
        return [_decrypt_audit_log(log) for log in results]

    @staticmethod
    def rotate_logs(
        db: Session,
        retention_months: int = 24,
        archive_path: str = "/app/data/audit_archive"
    ) -> dict:
        """
        Archivia e rimuove i log di audit più vecchi di retention_months.
        I campi criptati vengono decriptati prima dell'archiviazione.

        Args:
            db: SQLAlchemy session
            retention_months: Mesi di retention (default 24)
            archive_path: Directory per i file JSON archiviati

        Returns:
            dict con archived_count, archive_file, cutoff_date, remaining_count
            oppure dict con "error" in caso di eccezione
        """
        try:
            cutoff = datetime.now() - timedelta(days=retention_months * 30)

            # Conta record con created_at < cutoff
            count_to_archive_query = select(func.count()).select_from(AuditLog).where(AuditLog.created_at < cutoff)
            to_archive_count = db.execute(count_to_archive_query).scalar() or 0

            if to_archive_count == 0:
                total_remaining = db.execute(select(func.count()).select_from(AuditLog)).scalar() or 0
                return {
                    "archived_count": 0,
                    "archive_file": None,
                    "cutoff_date": cutoff.isoformat(),
                    "remaining_count": total_remaining
                }

            # a. Crea directory se non esiste
            os.makedirs(archive_path, exist_ok=True)

            # b. Query tutti i record con created_at < cutoff, ordinati per created_at ASC
            query = (
                select(AuditLog)
                .where(AuditLog.created_at < cutoff)
                .order_by(AuditLog.created_at.asc())
            )
            records = db.execute(query).scalars().all()

            # c. Per ogni record, creare dict con tutti i campi (decrypt prima)
            archive_data = []
            for log in records:
                _decrypt_audit_log(log)
                archive_data.append({
                    "id": log.id,
                    "user_id": log.user_id,
                    "username": log.username,
                    "action": log.action,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "details": log.details,
                    "old_value": log.old_value,
                    "new_value": log.new_value,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                })

            # d. Salva in file JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(archive_path, f"audit_logs_archived_{timestamp}.json")
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(archive_data, f, ensure_ascii=False, indent=2, default=str)

            # e. Elimina record archiviati
            db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))

            # f. Commit
            db.commit()

            # remaining_count dopo la cancellazione
            remaining_count = db.execute(select(func.count()).select_from(AuditLog)).scalar() or 0

            return {
                "archived_count": to_archive_count,
                "archive_file": filepath,
                "cutoff_date": cutoff.isoformat(),
                "remaining_count": remaining_count
            }

        except Exception as e:
            db.rollback()
            logger.error("Errore durante rotate_logs: %s", str(e))
            return {"error": str(e)}
