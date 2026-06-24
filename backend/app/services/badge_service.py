from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.badge import Badge, BadgeStatus, BadgeType
from app.models.person import Person
from app.models.site import Site
from app.schemas.badge import BadgeCreate, BadgeUpdate
from app.services.audit_service import AuditService
from fastapi import HTTPException, status
from typing import Optional
from datetime import date
import logging

logger = logging.getLogger(__name__)


class BadgeService:
    """Servizio per la gestione dei Badge aziendali"""

    @staticmethod
    def create_badge(db: Session, badge_data: BadgeCreate) -> Badge:
        """
        Crea un nuovo Badge

        Args:
            db: Sessione database
            badge_data: Dati Badge da creare

        Returns:
            Badge creato

        Raises:
            HTTPException: Se numero_badge già esiste
        """
        # Verifica unicità numero_badge
        existing = db.query(Badge).filter(Badge.numero_badge == badge_data.numero_badge).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Numero badge '{badge_data.numero_badge}' già esistente"
            )

        # Crea Badge
        db_badge = Badge(
            numero_badge=badge_data.numero_badge,
            tipo=badge_data.tipo,
            status=badge_data.status,
            data_emissione=badge_data.data_emissione,
            data_scadenza=badge_data.data_scadenza,
            site_id=badge_data.site_id,
            person_id=badge_data.person_id,
            notes=badge_data.notes,
            is_active=badge_data.is_active
        )

        db.add(db_badge)
        db.commit()
        db.refresh(db_badge)

        # Audit log
        try:
            AuditService.log_action(
                db=db,
                action="CREATE",
                entity_type="badge",
                entity_id=db_badge.id,
                details=f"Creato badge {db_badge.numero_badge} tipo {db_badge.tipo}",
                new_value={
                    "numero_badge": db_badge.numero_badge,
                    "tipo": db_badge.tipo,
                    "status": db_badge.status,
                    "person_id": db_badge.person_id,
                    "site_id": db_badge.site_id
                }
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        logger.info(f"Badge creato: {db_badge.numero_badge} - Tipo: {db_badge.tipo}")
        return db_badge

    @staticmethod
    def get_badge_by_id(db: Session, badge_id: int) -> Optional[Badge]:
        """Ottiene un Badge per ID"""
        return db.query(Badge).filter(Badge.id == badge_id).first()

    @staticmethod
    def get_badge_by_numero(db: Session, numero_badge: str) -> Optional[Badge]:
        """Ottiene un Badge per numero"""
        return db.query(Badge).filter(Badge.numero_badge == numero_badge).first()

    @classmethod
    def get_by_person_id(cls, db: Session, person_id: int) -> Optional[Badge]:
        """
        Recupera il Badge assegnato a una persona (attivo)
        """
        return db.query(Badge).filter(
            Badge.person_id == person_id,
            Badge.status == BadgeStatus.attivo,
            Badge.is_active == True
        ).first()

    @staticmethod
    def get_badges(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[BadgeStatus] = None,
        tipo: Optional[BadgeType] = None,
        site_id: Optional[int] = None,
        scaduti: Optional[bool] = None
    ) -> tuple[list[Badge], int]:
        """
        Ottiene lista Badge con filtri e paginazione

        Args:
            db: Sessione database
            skip: Numero record da saltare
            limit: Numero massimo record da restituire
            search: Ricerca in numero_badge, notes
            status: Filtra per status
            tipo: Filtra per tipo
            site_id: Filtra per sede
            scaduti: True=solo scaduti, False=solo validi, None=tutti

        Returns:
            Tupla (lista Badge, totale)
        """
        # Query con LEFT JOIN su person e site
        query = db.query(Badge).outerjoin(Person, Badge.person_id == Person.id).outerjoin(
            Site, Badge.site_id == Site.id
        ).options(
            joinedload(Badge.person),
            joinedload(Badge.site)
        )

        # Filtro ricerca
        if search:
            search_filter = or_(
                Badge.numero_badge.ilike(f"%{search}%"),
                Badge.notes.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)

        # Filtro status
        if status:
            query = query.filter(Badge.status == status)

        # Filtro tipo
        if tipo:
            query = query.filter(Badge.tipo == tipo)

        # Filtro sede
        if site_id:
            query = query.filter(Badge.site_id == site_id)

        # Filtro scaduti
        if scaduti is not None:
            oggi = date.today()
            if scaduti:
                # Solo badge scaduti
                query = query.filter(
                    Badge.data_scadenza.isnot(None),
                    Badge.data_scadenza < oggi
                )
            else:
                # Solo badge validi (senza scadenza o non ancora scaduti)
                query = query.filter(
                    or_(
                        Badge.data_scadenza.is_(None),
                        Badge.data_scadenza >= oggi
                    )
                )

        # Conta totale
        total = query.count()

        # Paginazione e ordinamento
        badges = query.order_by(Badge.created_at.desc()).offset(skip).limit(limit).all()

        return badges, total

    @staticmethod
    def update_badge(db: Session, badge_id: int, badge_data: BadgeUpdate) -> Badge:
        """
        Aggiorna un Badge esistente

        Args:
            db: Sessione database
            badge_id: ID Badge da aggiornare
            badge_data: Dati da aggiornare

        Returns:
            Badge aggiornato

        Raises:
            HTTPException: Se badge non trovato o numero_badge duplicato
        """
        db_badge = db.query(Badge).filter(Badge.id == badge_id).first()
        if not db_badge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Badge con ID {badge_id} non trovato"
            )

        # Salva old values per audit
        old_value = {
            "numero_badge": db_badge.numero_badge,
            "tipo": db_badge.tipo,
            "status": db_badge.status,
            "person_id": db_badge.person_id,
            "site_id": db_badge.site_id
        }

        # Verifica unicità numero_badge se modificato
        if badge_data.numero_badge and badge_data.numero_badge != db_badge.numero_badge:
            existing = db.query(Badge).filter(
                Badge.numero_badge == badge_data.numero_badge,
                Badge.id != badge_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Numero badge '{badge_data.numero_badge}' già esistente"
                )

        # Aggiorna campi forniti
        update_data = badge_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_badge, field, value)

        db.commit()

        # Audit log
        try:
            new_value = {
                "numero_badge": db_badge.numero_badge,
                "tipo": db_badge.tipo,
                "status": db_badge.status,
                "person_id": db_badge.person_id,
                "site_id": db_badge.site_id
            }
            AuditService.log_action(
                db=db,
                action="UPDATE",
                entity_type="badge",
                entity_id=db_badge.id,
                details=f"Aggiornato badge {db_badge.numero_badge}",
                old_value=old_value,
                new_value=new_value
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        db.refresh(db_badge)

        logger.info(f"Badge aggiornato: {db_badge.numero_badge}")
        return db_badge

    @staticmethod
    def delete_badge(db: Session, badge_id: int) -> bool:
        """
        Elimina (soft delete) un Badge

        Args:
            db: Sessione database
            badge_id: ID Badge da eliminare

        Returns:
            True se eliminato

        Raises:
            HTTPException: Se badge non trovato
        """
        db_badge = db.query(Badge).filter(Badge.id == badge_id).first()
        if not db_badge:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Badge con ID {badge_id} non trovato"
            )

        # Salva dati per audit
        numero_badge = db_badge.numero_badge

        db_badge.is_active = False
        db_badge.status = BadgeStatus.disattivo
        db.commit()

        # Audit log
        try:
            AuditService.log_action(
                db=db,
                action="DELETE",
                entity_type="badge",
                entity_id=db_badge.id,
                details=f"Badge disattivato (soft delete): {numero_badge}",
                old_value={"is_active": True}
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        logger.info(f"Badge eliminato (soft): {db_badge.numero_badge}")
        return True

    @staticmethod
    def get_scaduti(db: Session) -> list[Badge]:
        """
        Ottiene tutti i badge scaduti e ancora attivi

        Returns:
            Lista badge scaduti
        """
        oggi = date.today()
        return db.query(Badge).filter(
            Badge.data_scadenza.isnot(None),
            Badge.data_scadenza < oggi,
            Badge.is_active == True
        ).all()
