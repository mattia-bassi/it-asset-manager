from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.api.deps import get_db, get_current_user
from app.schemas.asset import Asset, AssetCreate, AssetUpdate, AssetList
from app.services.asset_service import AssetService
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.assignment import Assignment
from app.models.assignment_item import AssignmentItem
from app.models.person import Person
from app.models.asset import Asset as AssetModel
import json
import math
from fastapi.responses import FileResponse
from app.services.pdf_generator_service import PDFGeneratorService
from pathlib import Path

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=AssetList)
def get_assets(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    is_active: Optional[bool] = Query(None, description="Filtra per stato attivo"),
    asset_type_id: Optional[int] = Query(None, description="Filtra per tipo asset"),
    site_id: Optional[int] = Query(None, description="Filtra per sede"),
    person_id: Optional[int] = Query(None, description="Filtra per persona"),
    asset_status: Optional[str] = Query(None, description="Filtra per stato"),
    search: Optional[str] = Query(None, description="Ricerca per codice, seriale, marca, modello o MAC"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recupera la lista degli asset con paginazione e filtri."""
    # Inizializza person_id_filter con il parametro query
    person_id_filter = person_id

    # SECURITY: Se l'utente ha ruolo "user", può vedere SOLO i propri asset
    if current_user.role == 'user':
        if not current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utente non collegato a nessuna persona"
            )
        person_id_filter = current_user.person_id  # Forza filtro per person_id

    assets, total = AssetService.get_all(
        db=db,
        skip=skip,
        limit=limit,
        is_active=is_active,
        asset_type_id=asset_type_id,
        site_id=site_id,
        person_id=person_id_filter,
        status=asset_status,
        search=search
    )

    return {
        "items": assets,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit,
        "pages": math.ceil(total / limit) if limit > 0 else 1
    }


@router.get("/{asset_id}", response_model=Asset)
def get_asset(
    asset_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recupera un asset per ID."""
    asset = AssetService.get_by_id(db, asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset con ID {asset_id} non trovato"
        )
    
    # SECURITY: Se l'utente ha ruolo "user", può vedere SOLO i propri asset
    if current_user.role == 'user':
        if not current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Utente non collegato a nessuna persona"
            )
        if asset.person_id != current_user.person_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Non hai permesso di visualizzare questo asset"
            )
    
    return asset


@router.post("", response_model=Asset, status_code=status.HTTP_201_CREATED)
def create_asset(
    asset_data: AssetCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea un nuovo asset."""
    
    # SECURITY: Solo admin e operatore possono creare asset
    if current_user.role not in ['admin', 'operatore']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di creare asset"
        )
    
    try:
        asset = AssetService.create(db, asset_data)
        return asset
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{asset_id}", response_model=Asset)
def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggiorna un asset esistente."""
    
    # SECURITY: Solo admin e operatore possono modificare asset
    if current_user.role not in ['admin', 'operatore']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di modificare asset"
        )
    
    try:
        asset = AssetService.update(db, asset_id, asset_data)
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asset con ID {asset_id} non trovato"
            )
        return asset
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Disattiva un asset (soft delete)."""
    
    # SECURITY: Solo admin e operatore possono eliminare asset
    if current_user.role not in ['admin', 'operatore']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di eliminare asset"
        )
    
    success = AssetService.delete(db, asset_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset con ID {asset_id} non trovato"
        )


@router.delete("/{asset_id}/hard", status_code=status.HTTP_204_NO_CONTENT)
def hard_delete_asset(
    asset_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Elimina definitivamente un asset dal database."""
    
    # SECURITY: Solo admin può eliminare definitivamente
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo gli amministratori possono eliminare definitivamente gli asset"
        )
    
    success = AssetService.hard_delete(db, asset_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset con ID {asset_id} non trovato"
        )


@router.post("/{asset_id}/withdraw-for-maintenance")
def withdraw_asset_for_maintenance(
    asset_id: int,
    reason: str = None,
    notes: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ritira un asset assegnato e lo mette in manutenzione in modo atomico.
    Operazioni eseguite:
    1. Trova assignment attivo
    2. Imposta return_date = oggi
    3. Cambia assignment.status = 'completato'
    4. Cambia asset.status = 'manutenzione'
    5. Imposta asset.person_id = NULL
    6. Crea log audit
    Tutto in una transazione SQL atomica.
    """
    # SECURITY: Solo admin e operatore possono ritirare asset
    if current_user.role not in ['admin', 'operatore']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di ritirare asset per manutenzione"
        )
    
    try:
        # 1. Trova asset
        asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset non trovato"
            )
        
        # 2. Verifica che asset sia assegnato
        if not asset.person_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset non è attualmente assegnato a nessuno"
            )
        
        # 3. Trova assignment attivo
        active_assignment = db.query(Assignment).join(
            AssignmentItem, AssignmentItem.assignment_id == Assignment.id
        ).filter(
            AssignmentItem.asset_id == asset_id,
            Assignment.status == 'attivo'
        ).first()
        
        if not active_assignment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nessuna assegnazione attiva trovata per questo asset"
            )
        
        # 4. Ottieni persona per log
        person = db.query(Person).filter(Person.id == asset.person_id).first()
        person_name = f"{person.first_name} {person.last_name}" if person else "Unknown"
        
        # 5. OPERAZIONE ATOMICA: Aggiorna tutto in transazione
        # Chiudi assignment
        active_assignment.return_date = date.today()
        active_assignment.status = 'completato'
        
        # Cambia status asset e rimuovi assegnazione
        old_status = asset.status
        asset.status = 'manutenzione'
        asset.person_id = None
        
        # 6. Crea log audit
        audit_details = {
            'asset_code': asset.asset_code,
            'asset_name': f"{asset.manufacturer} {asset.model}",
            'serial_number': asset.serial_number,
            'person_name': person_name,
            'person_id': person.id if person else None,
            'old_status': old_status,
            'new_status': 'manutenzione',
            'reason': reason,
            'notes': notes,
            'assignment_id': active_assignment.id
        }
        
        audit_log = AuditLog(
            user_id=current_user.id,
            action='withdraw_for_maintenance',
            entity_type='asset',
            entity_id=asset_id,
            details=json.dumps(audit_details)
        )
        db.add(audit_log)
        
        # Commit transazione atomica
        db.commit()
        db.refresh(asset)
        
        return {
            'success': True,
            'message': f'Asset ritirato con successo e messo in manutenzione',
            'asset_id': asset_id,
            'asset_code': asset.asset_code,
            'previous_owner': person_name,
            'new_status': 'manutenzione'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il ritiro dell'asset: {str(e)}"
        )


@router.get("/{asset_id}/restitution-pdf")
def get_restitution_pdf(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Genera e restituisce il PDF del modulo di restituzione per un asset.
    Trova l'ultimo assignment completato e genera il documento formale.
    """
    # SECURITY: Solo admin e operatore possono generare PDF
    if current_user.role not in ['admin', 'operatore']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Non hai permesso di generare PDF di restituzione"
        )

    try:
        # 1. Trova asset
        asset = db.query(AssetModel).filter(AssetModel.id == asset_id).first()
        if not asset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset non trovato"
            )

        # 2. Trova ultimo assignment completato
        last_assignment = db.query(Assignment).join(
            AssignmentItem, AssignmentItem.assignment_id == Assignment.id
        ).filter(
            AssignmentItem.asset_id == asset_id,
            Assignment.status == 'completato',
            Assignment.return_date.isnot(None)
        ).order_by(Assignment.return_date.desc()).first()

        if not last_assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nessuna restituzione trovata per questo asset"
            )

        # 3. Ottieni dati persona
        person = db.query(Person).filter(Person.id == last_assignment.person_id).first()
        if not person:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Persona non trovata"
            )

        person_name = f"{person.first_name} {person.last_name}"
        person_site = person.site.name if person.site else None

        # 4. Ottieni dettagli audit per motivo e note
        audit_log = db.query(AuditLog).filter(
            AuditLog.entity_type == 'asset',
            AuditLog.entity_id == asset_id,
            AuditLog.action == 'withdraw_for_maintenance'
        ).order_by(AuditLog.created_at.desc()).first()

        reason = None
        notes = None
        if audit_log and audit_log.details:
            details = json.loads(audit_log.details)
            reason = details.get('reason')
            notes = details.get('notes')

        # 5. Genera PDF
        pdf_path = PDFGeneratorService.generate_restitution_pdf(
            asset_code=asset.asset_code or "N/A",
            asset_manufacturer=asset.manufacturer,
            asset_model=asset.model,
            asset_serial=asset.serial_number,
            person_name=person_name,
            person_site=person_site,
            assignment_date=last_assignment.assignment_date,
            restitution_date=last_assignment.return_date,
            reason=reason,
            notes=notes
        )

        # 6. Converti percorso relativo in assoluto
        full_path = Path("/app") / pdf_path.lstrip("/")
        
        if not full_path.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Errore nella generazione del PDF"
            )

        # 7. Restituisci file PDF
        filename = f"Restituzione_{asset.asset_code or asset.serial_number}_{last_assignment.return_date.strftime('%Y%m%d')}.pdf"
        
        return FileResponse(
            path=str(full_path),
            media_type="application/pdf",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante la generazione del PDF: {str(e)}"
        )
