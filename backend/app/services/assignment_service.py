from typing import Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, or_
from app.models.assignment import Assignment
from app.models.assignment_item import AssignmentItem
from app.models.asset import Asset
from app.models.inventory_sku import InventorySku
from app.models.sim import Sim
from app.models.location import Location
from app.models.person import Person
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate
from app.services.audit_service import AuditService

import logging

logger = logging.getLogger(__name__)


class AssignmentService:
    """Service per la gestione delle assegnazioni."""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        person_id: Optional[int] = None,
        status: Optional[str] = None,
        assignment_type: Optional[str] = None,
        active_only: bool = False
    ) -> tuple[list[dict], int, int]:
        """
        Recupera tutte le assegnazioni con filtri opzionali.
        Ritorna (lista_assegnazioni_con_dettagli, totale, conteggio_attive)
        """
        # Query base per conteggio (senza join per performance)
        count_query = select(Assignment)
        
        # Filtri per conteggio
        if person_id is not None:
            count_query = count_query.where(Assignment.person_id == person_id)
        
        if status:
            count_query = count_query.where(Assignment.status == status)
        
        if assignment_type:
            count_query = count_query.where(Assignment.assignment_type == assignment_type)
        
        if active_only:
            count_query = count_query.where(Assignment.status == 'attivo', Assignment.return_date.is_(None))
        
        # Conta totale
        total = db.scalar(select(func.count()).select_from(count_query.subquery()))
        
        # Query principale con join per dati
        query = select(
            Assignment,
            func.concat(Person.first_name, ' ', Person.last_name).label('person_name'),
            Person.email.label('person_email'),
            Location.name.label('location_name'),
            User.username.label('creator_name')
        ).outerjoin(Person, Assignment.person_id == Person.id
        ).outerjoin(Location, Assignment.location_id == Location.id
        ).outerjoin(User, Assignment.created_by == User.id)
        
        # Applica stessi filtri alla query principale
        if person_id is not None:
            query = query.where(Assignment.person_id == person_id)
        
        if status:
            query = query.where(Assignment.status == status)
        
        if assignment_type:
            query = query.where(Assignment.assignment_type == assignment_type)
        
        if active_only:
            query = query.where(Assignment.status == 'attivo', Assignment.return_date.is_(None))
        
        # Conta assegnazioni attive
        active_count = db.scalar(
            select(func.count()).select_from(Assignment).where(
                Assignment.status == 'attivo',
                Assignment.return_date.is_(None)
            )
        )
        
        # Paginazione e ordinamento
        query = query.order_by(Assignment.assignment_date.desc()).offset(skip).limit(limit)
        results = db.execute(query).all()
        
        # Converti in dizionari
        assignments_with_details = []
        for assignment, person_name, person_email, location_name, creator_name in results:
            # Carica items con eager loading
            items = db.scalars(
                select(AssignmentItem).where(AssignmentItem.assignment_id == assignment.id)
            ).all()
            
            assignment_dict = {
                "id": assignment.id,
                "person_id": assignment.person_id,
                "location_id": assignment.location_id,
                "assignment_date": assignment.assignment_date,
                "return_date": assignment.return_date,
                "assignment_type": assignment.assignment_type,
                "status": assignment.status,
                "notes": assignment.notes,
                "document_path": assignment.document_path,
                "created_by": assignment.created_by,
                "created_at": assignment.created_at,
                "updated_at": assignment.updated_at,
                "is_active": assignment.is_active,
                "assignment_number": assignment.assignment_number,
                "person_name": person_name if person_name else "",
                "person_email": person_email if person_email else None,
                "location_name": location_name if location_name else None,
                "creator_name": creator_name,
                "items": [
                    {
                        "id": item.id,
                        "assignment_id": item.assignment_id,
                        "item_type": item.item_type,
                        "asset_id": item.asset_id,
                        "inventory_sku_id": item.inventory_sku_id,
                        "sim_id": item.sim_id,
                        "quantity": item.quantity,
                        "notes": item.notes,
                        "item_description": item.item_description,
                        "is_returned": item.is_returned
                    }
                    for item in items
                ]
            }
            assignments_with_details.append(assignment_dict)
        
        return assignments_with_details, total or 0, active_count or 0

    @staticmethod
    def get_by_id(db: Session, assignment_id: int) -> Optional[Assignment]:
        """Recupera un'assegnazione per ID con location e person caricate."""
        return db.scalar(
            select(Assignment)
            .options(joinedload(Assignment.location), joinedload(Assignment.person))
            .where(Assignment.id == assignment_id)
        )

    @staticmethod
    def create(db: Session, assignment_data: AssignmentCreate, user_id: Optional[int] = None) -> Assignment:
        """
        Crea una nuova assegnazione.
        Aggiorna automaticamente:
        - Asset: status → 'assegnato', person_id, site_id
        - Inventory: quantity -= N
        """
        # Crea assignment
        assignment = Assignment(
            person_id=assignment_data.person_id,
            location_id=assignment_data.location_id,
            assignment_date=assignment_data.assignment_date,
            return_date=assignment_data.return_date,
            assignment_type=assignment_data.assignment_type,
            status=assignment_data.status,
            notes=assignment_data.notes,
            created_by=user_id
        )
        db.add(assignment)
        db.flush()  # Per ottenere l'ID
        
        # Se è sostituzione o riconsegna, chiudi assignment attivi precedenti
        if assignment_data.assignment_type in ['sostituzione', 'riconsegna']:
            # Trova tutti gli assignment attivi per questa persona o locazione
            active_filter = (
                (Assignment.person_id == assignment_data.person_id) if assignment_data.person_id is not None
                else (Assignment.location_id == assignment_data.location_id)
            )
            active_assignments = db.scalars(
                select(Assignment).where(
                    active_filter,
                    Assignment.status == 'attivo',
                    Assignment.id != assignment.id  # Escludi il nuovo assignment appena creato
                )
            ).all()
            
            # Chiudi tutti gli assignment attivi precedenti
            for old_assignment in active_assignments:
                old_assignment.status = 'completato'
                old_assignment.return_date = assignment_data.assignment_date
        
        # Carica persona per ottenere site_id (solo se destinatario è persona)
        person = None
        if assignment_data.person_id is not None:
            person = db.scalar(select(Person).where(Person.id == assignment_data.person_id))
        
        # Validazione: verifica che tutti gli asset siano assegnabili
        NON_ASSIGNABLE_STATUSES = ['manutenzione', 'riparazione', 'dismesso']
        
        for item_data in assignment_data.items:
            if item_data.item_type == 'asset' and item_data.asset_id:
                asset = db.scalar(select(Asset).where(Asset.id == item_data.asset_id))
                if not asset:
                    raise ValueError(f"Asset con ID {item_data.asset_id} non trovato")
                
                if asset.status in NON_ASSIGNABLE_STATUSES:
                    raise ValueError(
                        f"Impossibile assegnare l'asset '{asset.asset_code}': "
                        f"lo stato attuale è '{asset.status}'. "
                        f"Solo asset disponibili o in deposito possono essere assegnati."
                    )
                
                if asset.person_id is not None:
                    # Asset già assegnato ad altra persona
                    other_person = db.scalar(select(Person).where(Person.id == asset.person_id))
                    other_name = f"{other_person.first_name} {other_person.last_name}" if other_person else "un altro utente"
                    raise ValueError(
                        f"Impossibile assegnare l'asset '{asset.asset_code}': "
                        f"è già assegnato a {other_name}."
                    )
        
        # Crea items e aggiorna asset/inventory
        for item_data in assignment_data.items:
            # Crea item
            item = AssignmentItem(
                assignment_id=assignment.id,
                item_type=item_data.item_type,
                asset_id=item_data.asset_id,
                inventory_sku_id=item_data.inventory_sku_id,
                sim_id=item_data.sim_id,
                quantity=item_data.quantity,
                notes=item_data.notes
            )
            db.add(item)
            
            # Aggiorna asset (già validato sopra)
            if item_data.item_type == 'asset' and item_data.asset_id:
                asset = db.scalar(select(Asset).where(Asset.id == item_data.asset_id))
                if asset:
                    asset.status = 'assegnato'
                    if assignment_data.person_id is not None:
                        asset.person_id = assignment_data.person_id
                        asset.location_id = None
                        if person:
                            asset.site_id = person.site_id
                    elif assignment_data.location_id is not None:
                        asset.location_id = assignment_data.location_id
                        asset.person_id = None
                        # Update site_id from location's site
                        location = db.scalar(select(Location).where(Location.id == assignment_data.location_id))
                        if location and location.site_id:
                            asset.site_id = location.site_id
            
            # Aggiorna inventory
            if item_data.item_type == 'inventory' and item_data.inventory_sku_id:
                sku = db.scalar(select(InventorySku).where(InventorySku.id == item_data.inventory_sku_id))
                if sku:
                    if sku.quantity < item_data.quantity:
                        raise ValueError(f"Quantità insufficiente per {sku.device}: disponibili {sku.quantity}, richiesti {item_data.quantity}")
                    sku.quantity -= item_data.quantity

            # Aggiorna SIM (solo per assegnazione a persona)
            if item_data.item_type == 'sim' and item_data.sim_id:
                if assignment_data.person_id is None:
                    raise ValueError("Le SIM possono essere assegnate solo a persone, non a locazioni")
                sim = db.scalar(select(Sim).where(Sim.id == item_data.sim_id))
                if sim:
                    if sim.status != 'disponibile':
                        raise ValueError(f"SIM {sim.numero_telefono} non è disponibile (status: {sim.status})")
                    if sim.person_id is not None:
                        raise ValueError(f"SIM {sim.numero_telefono} è già assegnata")
                    sim.status = 'assegnata'
                    sim.person_id = assignment_data.person_id
                    # Aggiorna numero cellulare della persona
                    person = db.scalar(select(Person).where(Person.id == assignment_data.person_id))
                    if person:
                        person.mobile_phone = sim.numero_telefono

        # Gestisci items restituiti (per sostituzione/riconsegna)
        if assignment_data.returned_items:
            for ret_item_data in assignment_data.returned_items:
                ret_item = AssignmentItem(
                    assignment_id=assignment.id,
                    item_type=ret_item_data.item_type,
                    asset_id=ret_item_data.asset_id,
                    inventory_sku_id=ret_item_data.inventory_sku_id,
                    sim_id=ret_item_data.sim_id,
                    quantity=ret_item_data.quantity,
                    notes=ret_item_data.notes,
                    is_returned=True  # IMPORTANTE: marca come restituito
                )
                db.add(ret_item)
                
                # Se è un asset, ripristinalo (status → disponibile, person_id/location_id → NULL)
                if ret_item_data.item_type == 'asset' and ret_item_data.asset_id:
                    asset = db.scalar(select(Asset).where(Asset.id == ret_item_data.asset_id))
                    if asset:
                        asset.status = 'disponibile'
                        asset.person_id = None
                        asset.location_id = None

                # Se è una SIM, ripristinala (status → disponibile, person_id → NULL)
                if ret_item_data.item_type == 'sim' and ret_item_data.sim_id:
                    sim = db.scalar(select(Sim).where(Sim.id == ret_item_data.sim_id))
                    if sim:
                        sim.status = 'disponibile'
                        sim.person_id = None
        
        db.commit()
        db.refresh(assignment)

        # Audit log
        try:
            items_summary = f"{len(assignment_data.items)} item(s)"
            recipient_label = "persona" if assignment.person_id else "locazione"
            recipient_id = assignment.person_id or assignment.location_id
            AuditService.log_action(
                db=db,
                action="CREATE",
                entity_type="assignment",
                entity_id=assignment.id,
                details=f"Creata assegnazione {assignment.assignment_type} per {recipient_label} ID {recipient_id} - {items_summary}",
                new_value={
                    "assignment_type": assignment.assignment_type,
                    "person_id": assignment.person_id,
                    "location_id": assignment.location_id,
                    "status": assignment.status,
                    "items_count": len(assignment_data.items)
                }
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        return assignment

    @staticmethod
    def update(db: Session, assignment_id: int, assignment_data: AssignmentUpdate) -> Optional[Assignment]:
        """
        Aggiorna un'assegnazione esistente.
        Se viene impostata return_date, ripristina asset e inventory.
        """
        assignment = AssignmentService.get_by_id(db, assignment_id)
        if not assignment:
            return None
        
        # Se viene impostata return_date e prima era None, gestisci riconsegna
        if assignment_data.return_date and not assignment.return_date:
            AssignmentService._handle_return(db, assignment)
        
        # Aggiorna campi
        update_data = assignment_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(assignment, field, value)
        
        db.commit()
        db.refresh(assignment)
        return assignment

    @staticmethod
    def _handle_return(db: Session, assignment: Assignment):
        """
        Gestisce la riconsegna: ripristina asset, inventory e SIM (solo items non già restituiti).
        """
        items = db.scalars(
            select(AssignmentItem).where(AssignmentItem.assignment_id == assignment.id)
        ).all()
        
        for item in items:
            if item.is_returned:
                continue  # Già restituito (es. in sostituzione)
            # Ripristina asset
            if item.item_type == 'asset' and item.asset_id:
                asset = db.scalar(select(Asset).where(Asset.id == item.asset_id))
                if asset:
                    asset.status = 'disponibile'
                    asset.person_id = None
                    asset.location_id = None
                    # Site_id resta invariato
            
            # Ripristina inventory
            if item.item_type == 'inventory' and item.inventory_sku_id:
                sku = db.scalar(select(InventorySku).where(InventorySku.id == item.inventory_sku_id))
                if sku:
                    sku.quantity += item.quantity

            # Ripristina SIM
            if item.item_type == 'sim' and item.sim_id:
                sim = db.scalar(select(Sim).where(Sim.id == item.sim_id))
                if sim:
                    sim.status = 'disponibile'
                    sim.person_id = None
                    # Resetta numero cellulare della persona se corrisponde
                    if assignment.person_id:
                        person = db.scalar(select(Person).where(Person.id == assignment.person_id))
                        if person and person.mobile_phone == sim.numero_telefono:
                            person.mobile_phone = None

    @staticmethod
    def complete_assignment(db: Session, assignment_id: int, return_date: date) -> Optional[Assignment]:
        """
        Completa un'assegnazione impostando return_date e status='completato'.
        """
        return AssignmentService.update(
            db,
            assignment_id,
            AssignmentUpdate(return_date=return_date, status='completato')
        )

    @staticmethod
    def delete(db: Session, assignment_id: int) -> bool:
        """
        Elimina un'assegnazione (se non attiva).
        ATTENZIONE: Non ripristina asset/inventory, usare complete_assignment.
        """
        assignment = AssignmentService.get_by_id(db, assignment_id)
        if not assignment:
            return False
        
        if assignment.is_active:
            raise ValueError("Non è possibile eliminare un'assegnazione attiva. Completarla prima.")
        
        db.delete(assignment)
        db.commit()
        return True

