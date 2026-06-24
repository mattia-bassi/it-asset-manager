import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.models.person import Person
from app.models.asset import Asset
from app.models.assignment import Assignment
from app.models.sim import Sim
from app.models.badge import Badge
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService
from app.schemas.gdpr import (
    GDPRMyDataResponse,
    GDPRPortabilityResponse,
    GDPRRectificationRequest,
    GDPRRectificationResponse,
    GDPRErasureRequest,
    GDPRErasureResponse,
    GDPRRestrictionRequest,
    GDPRRestrictionResponse
)


class GDPRService:
    """Service per gestione diritti GDPR (Art. 15-20)"""

    # ========================================================================
    # GDPR Art. 15 - Right of Access (Diritto di Accesso)
    # ========================================================================

    @staticmethod
    def get_user_data(db: Session, user_id: int) -> GDPRMyDataResponse:
        """
        Export completo dati utente (GDPR Art. 15)

        Args:
            db: Database session
            user_id: ID utente richiedente

        Returns:
            GDPRMyDataResponse con tutti i dati dell'utente
        """
        try:
            # 1. Recupera dati utente
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"Utente {user_id} non trovato")

            # 2. Recupera person collegata (via user.person_id)
            person_data = None
            person = db.query(Person).filter(Person.id == user.person_id).first() if user.person_id else None
            if person:
                person_data = {
                    "id": person.id,
                    "first_name": person.first_name,
                    "last_name": person.last_name,
                    "email": person.email,
                    "phone": person.mobile_phone,
                    "department": None,
                    "job_title": None,
                    "created_at": person.created_at.isoformat() if person.created_at else None
                }

            # 3. Recupera asset assegnati
            assets_assigned = []
            if person:
                assets = db.query(Asset).filter(Asset.person_id == person.id).all()
                assets_assigned = [
                    {
                        "id": a.id,
                        "asset_code": a.asset_code,
                        "serial_number": a.serial_number,
                        "model": a.model,
                        "type": a.manufacturer,
                        "status": a.status,
                        "assigned_at": a.updated_at.isoformat() if a.updated_at else None
                    }
                    for a in assets
                ]

            # 4. Recupera storico assegnazioni
            assignments_history = []
            if person:
                assignments = db.query(Assignment).filter(Assignment.person_id == person.id).all()
                assignments_history = [
                    {
                        "id": a.id,
                        "asset_id": None,
                        "assigned_from": a.assignment_date.isoformat() if a.assignment_date else None,
                        "assigned_to": a.return_date.isoformat() if a.return_date else None,
                        "status": a.status
                    }
                    for a in assignments
                ]

            # 5. Recupera SIM assegnate
            sims_assigned = []
            if person:
                sims = db.query(Sim).filter(Sim.person_id == person.id).all()
                sims_assigned = [
                    {
                        "id": s.id,
                        "phone_number": s.numero_telefono,
                        "carrier": s.operatore,
                        "status": str(s.status) if s.status else None,
                        "assigned_at": s.updated_at.isoformat() if s.updated_at else None
                    }
                    for s in sims
                ]

            # 6. Recupera badge assegnati
            badges_assigned = []
            if person:
                badges = db.query(Badge).filter(Badge.person_id == person.id).all()
                badges_assigned = [
                    {
                        "id": b.id,
                        "badge_number": b.numero_badge,
                        "status": str(b.status) if b.status else None,
                        "assigned_at": b.updated_at.isoformat() if b.updated_at else None
                    }
                    for b in badges
                ]

            # 7. Recupera audit logs (ultime 100 azioni)
            audit_logs = db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(AuditLog.created_at.desc()).limit(100).all()
            audit_logs_data = [
                {
                    "id": log.id,
                    "action": log.action,
                    "entity_type": log.entity_type,
                    "entity_id": log.entity_id,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in audit_logs
            ]

            # 8. Email e full_name da Person (User non li ha)
            email = person.email if person else None
            full_name = person.full_name if person else user.username

            # 9. Crea response
            response = GDPRMyDataResponse(
                user_id=user.id,
                username=user.username,
                email=email,
                full_name=full_name,
                role=user.role,
                created_at=user.created_at,
                person=person_data,
                assets_assigned=assets_assigned,
                assignments_history=assignments_history,
                sims_assigned=sims_assigned,
                badges_assigned=badges_assigned,
                audit_logs=audit_logs_data,
                exported_at=datetime.now(),
                export_format="JSON"
            )

            # 10. Audit logging
            AuditService.log_action(
                db=db,
                action="GDPR_ACCESS",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                username=user.username,
                details=f"Export dati completato - {len(assets_assigned) + len(assignments_history) + len(sims_assigned) + len(badges_assigned)} record"
            )

            return response

        except Exception as e:
            AuditService.log_action(
                db=db,
                action="GDPR_ACCESS_ERROR",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                details=f"Errore export: {str(e)}"
            )
            raise

    # ========================================================================
    # GDPR Art. 20 - Right to Data Portability (Portabilità)
    # ========================================================================

    @staticmethod
    def export_portability(db: Session, user_id: int) -> GDPRPortabilityResponse:
        """
        Esportazione dati in formato portabile machine-readable (GDPR Art. 20)

        Args:
            db: Database session
            user_id: ID utente richiedente

        Returns:
            GDPRPortabilityResponse con dati in formato JSON portabile
        """
        try:
            # 1. Recupera dati utente
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"Utente {user_id} non trovato")

            person = db.query(Person).filter(Person.id == user.person_id).first() if user.person_id else None

            user_data = {
                "id": user.id,
                "username": user.username,
                "email": person.email if person else None,
                "full_name": person.full_name if person else user.username,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }

            # 2. Person data
            person_data = None
            if person:
                person_data = {
                    "id": person.id,
                    "first_name": person.first_name,
                    "last_name": person.last_name,
                    "email": person.email,
                    "phone": person.mobile_phone,
                    "department": None,
                    "job_title": None
                }

            # 3. Assets, Assignments, SIMs, Badges
            assets = []
            assignments = []
            sims = []
            badges = []

            if person:
                assets = [
                    {"id": a.id, "asset_code": a.asset_code, "serial_number": a.serial_number, "model": a.model, "type": a.manufacturer}
                    for a in db.query(Asset).filter(Asset.person_id == person.id).all()
                ]
                assignments = [
                    {"id": a.id, "assignment_date": a.assignment_date.isoformat() if a.assignment_date else None, "assigned_from": a.assignment_date.isoformat() if a.assignment_date else None}
                    for a in db.query(Assignment).filter(Assignment.person_id == person.id).all()
                ]
                sims = [
                    {"id": s.id, "phone_number": s.numero_telefono, "carrier": s.operatore}
                    for s in db.query(Sim).filter(Sim.person_id == person.id).all()
                ]
                badges = [
                    {"id": b.id, "badge_number": b.numero_badge}
                    for b in db.query(Badge).filter(Badge.person_id == person.id).all()
                ]

            # 4. Crea response
            response = GDPRPortabilityResponse(
                user_id=user.id,
                export_date=datetime.now(),
                data_format="JSON",
                user_data=user_data,
                person_data=person_data,
                assets=assets,
                assignments=assignments,
                sims=sims,
                badges=badges
            )

            # 5. Audit logging
            AuditService.log_action(
                db=db,
                action="GDPR_PORTABILITY",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                username=user.username,
                details=f"Export portabilità formato JSON - {len(assets) + len(assignments) + len(sims) + len(badges)} record"
            )

            return response

        except Exception as e:
            AuditService.log_action(
                db=db,
                action="GDPR_PORTABILITY_ERROR",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                details=f"Errore portabilità: {str(e)}"
            )
            raise

    # ========================================================================
    # GDPR Art. 16 - Right to Rectification (Rettifica)
    # ========================================================================

    @staticmethod
    def rectify_data(db: Session, user_id: int, rectification: GDPRRectificationRequest) -> GDPRRectificationResponse:
        """
        Rettifica dati personali (GDPR Art. 16)

        Args:
            db: Database session
            user_id: ID utente richiedente
            rectification: Dati da rettificare

        Returns:
            GDPRRectificationResponse con esito rettifica
        """
        try:
            updated_fields = []

            # 1. Recupera utente
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"Utente {user_id} non trovato")

            # 2. User non ha email/full_name - solo person. Aggiorna solo person
            person = db.query(Person).filter(Person.id == user.person_id).first() if user.person_id else None
            if not person:
                raise ValueError("Nessuna persona collegata all'utente - rettifica non applicabile")

            # 3. Aggiorna campi person
            if rectification.person_first_name:
                person.first_name = rectification.person_first_name
                updated_fields.append("person_first_name")
            if rectification.person_last_name:
                person.last_name = rectification.person_last_name
                updated_fields.append("person_last_name")
            if rectification.person_email:
                person.email = rectification.person_email
                updated_fields.append("person_email")
            if rectification.person_phone:
                person.mobile_phone = rectification.person_phone
                updated_fields.append("person_phone")
            if rectification.email:
                person.email = rectification.email
                updated_fields.append("email")
            if rectification.full_name:
                parts = rectification.full_name.strip().split(maxsplit=1)
                person.first_name = parts[0] if parts else person.first_name
                person.last_name = parts[1] if len(parts) > 1 else (person.last_name or "")
                updated_fields.append("full_name")

            # 4. Commit modifiche
            db.commit()

            # 5. Audit logging
            AuditService.log_action(
                db=db,
                action="GDPR_RECTIFICATION",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                username=user.username,
                details=json.dumps({"updated_fields": updated_fields, "reason": rectification.reason}, ensure_ascii=False)
            )

            # 6. Crea response
            response = GDPRRectificationResponse(
                success=True,
                message=f"Dati rettificati con successo. Campi aggiornati: {', '.join(updated_fields)}",
                updated_fields=updated_fields,
                updated_at=datetime.now()
            )

            return response

        except Exception as e:
            db.rollback()
            AuditService.log_action(
                db=db,
                action="GDPR_RECTIFICATION_ERROR",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                details=f"Errore rettifica: {str(e)}"
            )
            raise

    # ========================================================================
    # GDPR Art. 17 - Right to Erasure (Cancellazione)
    # ========================================================================

    @staticmethod
    def erase_user_data(db: Session, user_id: int, erasure: GDPRErasureRequest) -> GDPRErasureResponse:
        """
        Cancellazione account e dati personali (GDPR Art. 17 - Right to be forgotten)

        IMPORTANTE: Per compliance audit, i dati vengono anonimizzati invece di cancellati fisicamente.
        Gli audit logs devono essere mantenuti per tracciabilità legale.

        Args:
            db: Database session
            user_id: ID utente richiedente
            erasure: Richiesta cancellazione

        Returns:
            GDPRErasureResponse con esito cancellazione
        """
        try:
            # 1. Verifica conferma
            if not erasure.confirm_deletion:
                raise ValueError("Conferma cancellazione richiesta (confirm_deletion=True)")

            # 2. Recupera utente
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"Utente {user_id} non trovato")

            # 3. Salva person_id prima di scollegare
            old_person_id = user.person_id

            # 4. Anonimizza dati utente
            user.username = f"deleted_user_{user_id}"
            user.password_hash = "DELETED"
            user.is_active = False
            user.person_id = None  # Scollega da person

            # 5. Anonimizza person collegata (se esiste)
            if old_person_id:
                person = db.query(Person).filter(Person.id == old_person_id).first()
                if person:
                    person.first_name = "DELETED"
                    person.last_name = "DELETED"
                    person.email = f"deleted_{person.id}@anonymized.local"
                    person.mobile_phone = "DELETED"
                    person.is_active = False

            db.commit()

            # 6. Audit logging (CRITICO - deve essere fatto DOPO commit)
            AuditService.log_action(
                db=db,
                action="GDPR_ERASURE",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                details=json.dumps({"reason": erasure.reason, "anonymized": True, "deleted_at": datetime.now().isoformat()}, ensure_ascii=False)
            )

            # 7. Response
            response = GDPRErasureResponse(
                success=True,
                message="Account cancellato con successo. I dati sono stati anonimizzati per compliance legale.",
                user_id=user_id,
                anonymized=True,
                deleted_at=datetime.now()
            )

            return response

        except Exception as e:
            db.rollback()
            AuditService.log_action(
                db=db,
                action="GDPR_ERASURE_ERROR",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                details=f"Errore cancellazione: {str(e)}"
            )
            raise

    # ========================================================================
    # GDPR Art. 18 - Right to Restriction (Limitazione Trattamento)
    # ========================================================================

    @staticmethod
    def restrict_processing(db: Session, user_id: int, restriction: GDPRRestrictionRequest) -> GDPRRestrictionResponse:
        """
        Limitazione trattamento dati (GDPR Art. 18)

        Implementazione: disabilita l'account temporaneamente o permanentemente

        Args:
            db: Database session
            user_id: ID utente richiedente
            restriction: Richiesta limitazione

        Returns:
            GDPRRestrictionResponse con esito limitazione
        """
        try:
            # 1. Recupera utente
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"Utente {user_id} non trovato")

            # 2. Applica restrizione (disabilita account)
            user.is_active = False

            # 3. Commit
            db.commit()

            # 4. Audit logging
            AuditService.log_action(
                db=db,
                action="GDPR_RESTRICTION",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                username=user.username,
                details=json.dumps({
                    "reason": restriction.reason,
                    "restriction_type": restriction.restriction_type,
                    "restricted_at": datetime.now().isoformat()
                }, ensure_ascii=False)
            )

            # 5. Response
            response = GDPRRestrictionResponse(
                success=True,
                message=f"Limitazione trattamento attivata ({restriction.restriction_type}). Account disabilitato.",
                user_id=user_id,
                restriction_active=True,
                restriction_type=restriction.restriction_type,
                restricted_at=datetime.now()
            )

            return response

        except Exception as e:
            db.rollback()
            AuditService.log_action(
                db=db,
                action="GDPR_RESTRICTION_ERROR",
                entity_type="user",
                entity_id=user_id,
                user_id=user_id,
                details=f"Errore limitazione: {str(e)}"
            )
            raise
