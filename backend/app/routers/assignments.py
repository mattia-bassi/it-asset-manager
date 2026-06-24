from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from datetime import date
from app.api.deps import get_db, get_current_user
from app.schemas.assignment import Assignment, AssignmentCreate, AssignmentUpdate, AssignmentList
from app.services.assignment_service import AssignmentService
from app.models.user import User
import logging
import math

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get("", response_model=AssignmentList)
def get_assignments(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    person_id: Optional[int] = Query(None, description="Filtra per persona"),
    status: Optional[str] = Query(None, description="Filtra per stato"),
    assignment_type: Optional[str] = Query(None, description="Filtra per tipo"),
    active_only: bool = Query(False, description="Solo assegnazioni attive"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recupera la lista delle assegnazioni con paginazione e filtri."""
    # Inizializza person_id_filter con il parametro query
    person_id_filter = person_id

    # SECURITY: Se l'utente ha ruolo "user", può vedere SOLO le proprie assegnazioni
    if current_user.role == 'user':
        if not current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utente non collegato a nessuna persona"
            )
        person_id_filter = current_user.person_id  # Forza filtro per person_id

    assignments, total, active_count = AssignmentService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        person_id=person_id_filter,
        status=status,
        assignment_type=assignment_type,
        active_only=active_only
    )

    return {
        "items": assignments,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
        "pages": math.ceil(total / limit) if limit > 0 else 1,
        "active_count": active_count
    }


@router.get("/{assignment_id}", response_model=Assignment)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recupera un'assegnazione per ID."""
    assignment = AssignmentService.get_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assegnazione con ID {assignment_id} non trovata"
        )
    
    # SECURITY: Se l'utente ha ruolo "user", può vedere SOLO le proprie assegnazioni
    if current_user.role == 'user':
        if not current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utente non collegato a nessuna persona"
            )
        if assignment.person_id != current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai permesso di visualizzare questa assegnazione"
            )
    
    return assignment


@router.post("", response_model=Assignment, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea una nuova assegnazione.
    Aggiorna automaticamente asset (status → 'assegnato') e inventory (quantity - N).
    """
    
    # SECURITY: Solo admin e operatore possono creare assegnazioni
    if current_user.role not in ['admin', 'operatore']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di creare assegnazioni"
        )
    
    try:
        assignment = AssignmentService.create(db, assignment_data, current_user.id)
        return assignment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{assignment_id}", response_model=Assignment)
def update_assignment(
    assignment_id: int,
    assignment_data: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aggiorna un'assegnazione esistente.
    Se viene impostata return_date, ripristina automaticamente asset e inventory.
    """
    
    # SECURITY: Solo admin e operatore possono modificare assegnazioni
    if current_user.role not in ['admin', 'operatore']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di modificare assegnazioni"
        )
    
    try:
        assignment = AssignmentService.update(db, assignment_id, assignment_data)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assegnazione con ID {assignment_id} non trovata"
            )
        return assignment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{assignment_id}/complete", response_model=Assignment)
def complete_assignment(
    assignment_id: int,
    return_date: date = Query(..., description="Data riconsegna"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Completa un'assegnazione impostando return_date e status='completato'.
    Ripristina automaticamente asset (disponibili) e inventory (quantità).
    """
    
    # SECURITY: Solo admin e operatore possono completare assegnazioni
    if current_user.role not in ['admin', 'operatore']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di completare assegnazioni"
        )
    
    try:
        assignment = AssignmentService.complete_assignment(db, assignment_id, return_date)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assegnazione con ID {assignment_id} non trovata"
            )
        return assignment
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina un'assegnazione (solo se non attiva).
    ATTENZIONE: Non ripristina asset/inventory. Usare prima /complete.
    """
    
    # SECURITY: Solo admin e operatore possono eliminare assegnazioni
    if current_user.role not in ['admin', 'operatore']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di eliminare assegnazioni"
        )
    
    try:
        success = AssignmentService.delete(db, assignment_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assegnazione con ID {assignment_id} non trovata"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )



from fastapi.responses import FileResponse
from app.schemas.pdf_request import PDFGenerateRequest
from app.services.pdf_generator_service import PDFGeneratorService
from app.services.document_template_service import DocumentTemplateService
from app.services.person_service import PersonService
from pathlib import Path


@router.post("/{assignment_id}/generate-pdf")
def generate_assignment_pdf(
    assignment_id: int,
    pdf_data: PDFGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera il PDF del foglio di assegnazione.
    Include logo/footer dal template di default e i dati dell'assegnazione.
    """
    
    # Recupera assegnazione
    assignment = AssignmentService.get_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assegnazione con ID {assignment_id} non trovata"
        )
    
    # SECURITY: Verifica permessi
    if current_user.role == 'user':
        # User può generare PDF solo delle proprie assegnazioni
        if not current_user.person_id or assignment.person_id != current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai permesso di generare il PDF per questa assegnazione"
            )

    # Recupera persona
    person = PersonService.get_by_id(db, assignment.person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona non trovata"
        )

    # Recupera template di default per logo/footer
    template = DocumentTemplateService.get_default(db)
    logo_path = template.logo_path if template else None
    footer_path = template.footer_path if template else None

    # Recupera nome sede se presente
    site_name = None
    if person.site_id:
        from app.services.site_service import SiteService
        site = SiteService.get_by_id(db, person.site_id)
        site_name = site.name if site else None

    # Recupera SIM assegnata alla persona (se esiste)
    person_mobile_phone = None
    try:
        from app.services.sim_service import SimService
        sim = SimService.get_by_person_id(db, person.id)
        if sim:
            person_mobile_phone = sim.numero_telefono
    except Exception as e:
        logger.warning("Errore recupero SIM per persona %s: %s", person.id, e)

    # Prepara lista items per il PDF
    items = []
    for item in assignment.items:
        # Determina il tipo di item
        if item.item_type == 'asset':
            item_type = 'Asset'
        elif item.item_type == 'sim':
            item_type = 'SIM'
        else:
            item_type = 'Materiale'

        item_dict = {
            'type': item_type,
            'description': item.item_description,
            'quantity': item.quantity,
            'serial': None
        }

        # Se è un asset, recupera il serial number
        if item.item_type == 'asset' and item.asset_id:
            from app.services.asset_service import AssetService
            asset = AssetService.get_by_id(db, item.asset_id)
            if asset:
                item_dict['serial'] = asset.serial_number

        # Se è una SIM, recupera i dettagli
        if item.item_type == 'sim' and item.sim_id:
            from app.models.sim import Sim
            sim = db.scalar(select(Sim).where(Sim.id == item.sim_id))
            if sim:
                item_dict['serial'] = sim.seriale
                item_dict['sim_operator'] = sim.operatore
                item_dict['sim_number'] = sim.numero_telefono

        items.append(item_dict)

    # Decripta automaticamente PIN SIM se presente nell'assegnazione
    decrypted_pin_sim = pdf_data.pin_sim  # Default: usa quello fornito dal frontend (retrocompatibilità)
    for item in assignment.items:
        if item.item_type == 'sim' and item.sim_id:
            try:
                from app.services.sim_service import SimService
                credentials = SimService.get_sim_credentials(db, item.sim_id)
                decrypted_pin_sim = credentials.get('pin', '')
                break  # Prendi solo il PIN della prima SIM trovata
            except Exception as e:
                logger.error("Errore decriptazione PIN SIM %s: %s", item.sim_id, e)
                # Mantieni il PIN dal frontend se la decriptazione fallisce

    # Genera PDF
    try:
        pdf_path = PDFGeneratorService.generate_assignment_pdf(
            assignment_number=assignment.assignment_number,
            assignment_date=assignment.assignment_date,
            person_name=f"{person.first_name} {person.last_name}",
            person_email=person.email or "",
            person_extension=person.extension or "",
            person_mobile_phone=person_mobile_phone or "",
            person_department=None,
            person_site=site_name or "",
            items=items,
            password=pdf_data.password,
            pin_sim=decrypted_pin_sim,
            pin_sblocco=pdf_data.pin_sblocco,
            notes=assignment.notes,
            logo_path=logo_path,
            footer_path=footer_path
        )

        # Aggiorna assegnazione con path documento
        from app.schemas.assignment import AssignmentUpdate
        AssignmentService.update(db, assignment_id, AssignmentUpdate(document_path=pdf_path))

        # Ritorna il file
        full_path = Path("/app") / pdf_path.lstrip("/")
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore nella generazione del PDF"
            )

        return FileResponse(
            path=str(full_path),
            filename=f"{assignment.assignment_number.replace('/', '-')}.pdf",
            media_type="application/pdf"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore generazione PDF: {str(e)}"
        )


@router.post("/{assignment_id}/generate-substitution-pdf")
def generate_substitution_pdf(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera il PDF del modulo di sostituzione.
    Include sia materiale restituito che materiale assegnato.
    """
    # Recupera assegnazione
    assignment = AssignmentService.get_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assegnazione con ID {assignment_id} non trovata"
        )
    
    # Verifica che sia di tipo sostituzione
    if assignment.assignment_type != 'sostituzione':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questo endpoint è solo per assegnazioni di tipo 'sostituzione'"
        )
    
    # SECURITY: Verifica permessi
    if current_user.role == 'user':
        if not current_user.person_id or assignment.person_id != current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai permesso di generare il PDF per questa assegnazione"
            )
    
    # Recupera persona
    person = PersonService.get_by_id(db, assignment.person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona non trovata"
        )
    
    # Recupera template di default per logo/footer
    template = DocumentTemplateService.get_default(db)
    logo_path = template.logo_path if template else None
    footer_path = template.footer_path if template else None
    
    # Recupera nome sede se presente
    site_name = None
    if person.site_id:
        from app.services.site_service import SiteService
        site = SiteService.get_by_id(db, person.site_id)
        site_name = site.name if site else None
    
    # Recupera SIM assegnata alla persona (se esiste)
    person_mobile_phone = None
    try:
        from app.services.sim_service import SimService
        sim = SimService.get_by_person_id(db, person.id)
        if sim:
            person_mobile_phone = sim.numero_telefono
    except Exception as e:
        logger.warning("Errore recupero SIM per persona %s: %s", person.id, e)
    
    # Prepara lista items ASSEGNATI (filtrati con is_returned=False)
    assigned_items = []
    for item in assignment.items:
        if not item.is_returned:  # filtra solo items assegnati
            if item.item_type == 'asset':
                item_type = 'Asset'
            elif item.item_type == 'sim':
                item_type = 'SIM'
            else:
                item_type = 'Materiale'
            item_dict = {
                'type': item_type,
                'description': item.item_description,
                'quantity': item.quantity,
                'serial': None
            }
            if item.item_type == 'asset' and item.asset_id:
                from app.services.asset_service import AssetService
                asset = AssetService.get_by_id(db, item.asset_id)
                if asset:
                    item_dict['serial'] = asset.serial_number
            if item.item_type == 'sim' and item.sim_id:
                from app.models.sim import Sim
                sim = db.scalar(select(Sim).where(Sim.id == item.sim_id))
                if sim:
                    item_dict['serial'] = sim.seriale
                    item_dict['sim_operator'] = sim.operatore
                    item_dict['sim_number'] = sim.numero_telefono
            assigned_items.append(item_dict)
    
    # Prepara lista items RESTITUITI (filtrati con is_returned=True)
    returned_items = []
    for item in assignment.items:
        if item.is_returned:
            if item.item_type == 'asset':
                ret_item_type = 'Asset'
            elif item.item_type == 'sim':
                ret_item_type = 'SIM'
            else:
                ret_item_type = 'Materiale'
            ret_item_dict = {
                'type': ret_item_type,
                'description': item.item_description,
                'quantity': item.quantity,
                'serial': None
            }
            if item.item_type == 'asset' and item.asset_id:
                from app.services.asset_service import AssetService
                asset = AssetService.get_by_id(db, item.asset_id)
                if asset:
                    ret_item_dict['serial'] = asset.serial_number
            if item.item_type == 'sim' and item.sim_id:
                from app.models.sim import Sim
                sim = db.scalar(select(Sim).where(Sim.id == item.sim_id))
                if sim:
                    ret_item_dict['serial'] = sim.seriale
                    ret_item_dict['sim_operator'] = sim.operatore
                    ret_item_dict['sim_number'] = sim.numero_telefono
            returned_items.append(ret_item_dict)

    # Decripta automaticamente PIN SIM se presente negli items assegnati
    decrypted_pin_sim = None
    for item in assignment.items:
        if not item.is_returned and item.item_type == 'sim' and item.sim_id:
            try:
                from app.services.sim_service import SimService
                credentials = SimService.get_sim_credentials(db, item.sim_id)
                decrypted_pin_sim = credentials.get('pin', '')
                break  # Prendi solo il PIN della prima SIM assegnata
            except Exception as e:
                logger.error("Errore decriptazione PIN SIM %s: %s", item.sim_id, e)

    # Genera PDF
    try:
        pdf_path = PDFGeneratorService.generate_substitution_pdf(
            assignment_number=assignment.assignment_number,
            assignment_date=assignment.assignment_date,
            person_name=f"{person.first_name} {person.last_name}",
            person_email=person.email or "",
            person_extension=person.extension or "",
            person_mobile_phone=person_mobile_phone or "",
            person_site=site_name or "",
            returned_items=returned_items,
            assigned_items=assigned_items,
            notes=assignment.notes or "",
            logo_path=logo_path,
            footer_path=footer_path,
            pin_sim=decrypted_pin_sim
        )
        
        # Aggiorna assegnazione con path documento
        from app.schemas.assignment import AssignmentUpdate
        AssignmentService.update(db, assignment_id, AssignmentUpdate(document_path=pdf_path))
        
        # Ritorna il file
        full_path = Path("/app") / pdf_path.lstrip("/")
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore nella generazione del PDF"
            )
        
        return FileResponse(
            path=str(full_path),
            filename=f"{assignment.assignment_number.replace('/', '-')}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore generazione PDF: {str(e)}"
        )


@router.post("/{assignment_id}/generate-return-pdf")
def generate_return_pdf(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera il PDF del modulo di riconsegna materiale.
    Include SOLO materiale restituito (NO assegnazione, NO credenziali).
    """
    # Recupera assegnazione
    assignment = AssignmentService.get_by_id(db, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assegnazione con ID {assignment_id} non trovata"
        )

    # Verifica che sia di tipo riconsegna
    if assignment.assignment_type != 'riconsegna':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Questo endpoint è solo per assegnazioni di tipo 'riconsegna'"
        )

    # SECURITY: Verifica permessi
    if current_user.role == 'user':
        if not current_user.person_id or assignment.person_id != current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai permesso di generare il PDF per questa assegnazione"
            )

    # Recupera persona
    person = PersonService.get_by_id(db, assignment.person_id)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Persona non trovata"
        )

    # Recupera template di default per logo/footer
    template = DocumentTemplateService.get_default(db)
    logo_path = template.logo_path if template else None
    footer_path = template.footer_path if template else None

    # Recupera nome sede se presente
    site_name = None
    if person.site_id:
        from app.services.site_service import SiteService
        site = SiteService.get_by_id(db, person.site_id)
        site_name = site.name if site else None

    # Recupera SIM assegnata alla persona (se esiste)
    person_mobile_phone = None
    try:
        from app.services.sim_service import SimService
        sim = SimService.get_by_person_id(db, person.id)
        if sim:
            person_mobile_phone = sim.numero_telefono
    except Exception as e:
        logger.error("Errore recupero SIM per persona %s: %s", person.id, e)

    # Prepara lista items RESTITUITI (filtrati con is_returned=True)
    # Per la riconsegna, TUTTI gli items dovrebbero essere restituiti
    returned_items = []
    for item in assignment.items:
        if item.is_returned:
            if item.item_type == 'asset':
                ret_item_type = 'Asset'
            elif item.item_type == 'sim':
                ret_item_type = 'SIM'
            else:
                ret_item_type = 'Materiale'

            ret_item_dict = {
                'type': ret_item_type,
                'description': item.item_description,
                'quantity': item.quantity,
                'serial': None
            }

            if item.item_type == 'asset' and item.asset_id:
                from app.services.asset_service import AssetService
                asset = AssetService.get_by_id(db, item.asset_id)
                if asset:
                    ret_item_dict['serial'] = asset.serial_number

            if item.item_type == 'sim' and item.sim_id:
                from app.models.sim import Sim
                sim = db.scalar(select(Sim).where(Sim.id == item.sim_id))
                if sim:
                    ret_item_dict['serial'] = sim.seriale
                    ret_item_dict['sim_operator'] = sim.operatore
                    ret_item_dict['sim_number'] = sim.numero_telefono

            returned_items.append(ret_item_dict)

    # Verifica che ci siano items da restituire
    if not returned_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nessun materiale da restituire trovato per questa riconsegna"
        )

    # Genera PDF
    try:
        pdf_path = PDFGeneratorService.generate_return_pdf(
            assignment_number=assignment.assignment_number,
            assignment_date=assignment.assignment_date,
            person_name=f"{person.first_name} {person.last_name}",
            person_email=person.email or "",
            person_extension=person.extension or "",
            person_mobile_phone=person_mobile_phone or "",
            person_site=site_name or "",
            returned_items=returned_items,
            notes=assignment.notes,
            logo_path=logo_path,
            footer_path=footer_path
        )

        # Aggiorna assegnazione con path documento
        from app.schemas.assignment import AssignmentUpdate
        AssignmentService.update(db, assignment_id, AssignmentUpdate(document_path=pdf_path))

        # Ritorna il file
        full_path = Path("/app") / pdf_path.lstrip("/")
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore nella generazione del PDF"
            )

        return FileResponse(
            path=str(full_path),
            filename=f"{assignment.assignment_number.replace('/', '-')}.pdf",
            media_type="application/pdf"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore generazione PDF: {str(e)}"
        )
