from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.site import Site
from app.schemas.site import SiteCreate, SiteUpdate


class SiteService:
    """Service per la gestione delle sedi."""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> tuple[list[Site], int]:
        """
        Recupera tutte le sedi con filtri opzionali.
        Ritorna (lista_sedi, totale)
        """
        query = select(Site)
        
        # Filtro attivo/inattivo
        if is_active is not None:
            query = query.where(Site.is_active == is_active)
        
        # Ricerca per nome o città
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (Site.name.ilike(search_term)) | 
                (Site.city.ilike(search_term))
            )
        
        # Conta totale (prima di paginazione)
        total = db.scalar(select(func.count()).select_from(query.subquery()))
        
        # Paginazione e ordinamento
        query = query.order_by(Site.name).offset(skip).limit(limit)
        sites = db.scalars(query).all()
        
        return list(sites), total or 0

    @staticmethod
    def get_by_id(db: Session, site_id: int) -> Optional[Site]:
        """Recupera una sede per ID."""
        return db.scalar(select(Site).where(Site.id == site_id))

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[Site]:
        """Recupera una sede per nome (case-insensitive)."""
        return db.scalar(select(Site).where(func.lower(Site.name) == name.lower()))

    @staticmethod
    def create(db: Session, site_data: SiteCreate) -> Site:
        """Crea una nuova sede."""
        # Verifica duplicati
        existing = SiteService.get_by_name(db, site_data.name)
        if existing:
            raise ValueError(f"Esiste già una sede con nome '{site_data.name}'")
        
        site = Site(**site_data.model_dump())
        db.add(site)
        db.commit()
        db.refresh(site)
        return site

    @staticmethod
    def update(db: Session, site_id: int, site_data: SiteUpdate) -> Optional[Site]:
        """Aggiorna una sede esistente."""
        site = SiteService.get_by_id(db, site_id)
        if not site:
            return None
        
        # Verifica duplicati sul nome se viene modificato
        if site_data.name and site_data.name != site.name:
            existing = SiteService.get_by_name(db, site_data.name)
            if existing and existing.id != site_id:
                raise ValueError(f"Esiste già una sede con nome '{site_data.name}'")
        
        # Aggiorna solo i campi forniti
        update_data = site_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(site, field, value)
        
        db.commit()
        db.refresh(site)
        return site

    @staticmethod
    def delete(db: Session, site_id: int) -> bool:
        """Elimina una sede (soft delete: is_active=False)."""
        site = SiteService.get_by_id(db, site_id)
        if not site:
            return False
        
        site.is_active = False
        db.commit()
        return True

    @staticmethod
    def hard_delete(db: Session, site_id: int) -> bool:
        """Elimina definitivamente una sede dal database."""
        site = SiteService.get_by_id(db, site_id)
        if not site:
            return False
        
        db.delete(site)
        db.commit()
        return True

