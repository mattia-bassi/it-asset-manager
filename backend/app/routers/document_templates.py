import logging
logger = logging.getLogger(__name__)
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import shutil
from pathlib import Path
from app.api.deps import get_db, get_current_user, get_current_active_admin
from app.schemas.document_template import (
    DocumentTemplate,
    DocumentTemplateCreate,
    DocumentTemplateUpdate
)
from app.services.document_template_service import DocumentTemplateService
from app.models.user import User

router = APIRouter(prefix="/document-templates", tags=["Document Templates"])

# Directory base per i file uploadati
UPLOAD_BASE_DIR = Path("/app/data/templates")
LOGOS_DIR = UPLOAD_BASE_DIR / "logos"
FOOTERS_DIR = UPLOAD_BASE_DIR / "footers"

# Estensioni file permesse
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".svg"}


def validate_image_file(file: UploadFile) -> None:
    """Valida che il file sia un'immagine valida"""
    # Verifica estensione
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato file non supportato. Usare: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Verifica content type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Il file deve essere un'immagine"
        )


@router.get("", response_model=List[DocumentTemplate])
def get_templates(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recupera tutti i template"""
    return DocumentTemplateService.get_all(db, skip=skip, limit=limit, active_only=active_only)


@router.get("/default", response_model=DocumentTemplate)
def get_default_template(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Recupera il template predefinito"""
    template = DocumentTemplateService.get_default(db)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nessun template predefinito trovato"
        )
    return template


@router.get("/{template_id}", response_model=DocumentTemplate)
def get_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Recupera un template per ID"""
    template = DocumentTemplateService.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} non trovato"
        )
    return template


@router.post("", response_model=DocumentTemplate, status_code=status.HTTP_201_CREATED)
def create_template(
    template: DocumentTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Crea un nuovo template"""
    return DocumentTemplateService.create(db, template)


@router.put("/{template_id}", response_model=DocumentTemplate)
def update_template(
    template_id: int,
    template: DocumentTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggiorna un template esistente"""
    updated_template = DocumentTemplateService.update(db, template_id, template)
    if not updated_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} non trovato"
        )
    return updated_template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Soft delete di un template"""
    success = DocumentTemplateService.delete(db, template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile eliminare il template (potrebbe essere predefinito o non esistente)"
        )
    return None


@router.post("/{template_id}/set-default", response_model=DocumentTemplate)
def set_default_template(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Imposta un template come predefinito"""
    template = DocumentTemplateService.set_default(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} non trovato o non attivo"
        )
    return template


@router.post("/{template_id}/upload-logo", response_model=DocumentTemplate)
async def upload_logo(
    template_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Upload logo per un template"""
    # Verifica che il template esista
    template = DocumentTemplateService.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} non trovato"
        )
    
    # Valida il file
    validate_image_file(file)
    
    # Crea directory se non esiste
    LOGOS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Genera nome file univoco
    file_ext = Path(file.filename).suffix.lower()
    filename = f"logo_{template_id}{file_ext}"
    file_path = LOGOS_DIR / filename
    
    # Salva il file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il salvataggio del file: {str(e)}"
        )
    
    # Aggiorna il template con il path del logo
    relative_path = f"/data/templates/logos/{filename}"
    update_data = DocumentTemplateUpdate(logo_path=relative_path)
    updated_template = DocumentTemplateService.update(db, template_id, update_data)
    
    return updated_template


@router.post("/{template_id}/upload-footer", response_model=DocumentTemplate)
async def upload_footer(
    template_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_admin)
):
    """Upload footer per un template"""
    # Verifica che il template esista
    template = DocumentTemplateService.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} non trovato"
        )
    
    # Valida il file
    validate_image_file(file)
    
    # Crea directory se non esiste
    FOOTERS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Genera nome file univoco
    file_ext = Path(file.filename).suffix.lower()
    filename = f"footer_{template_id}{file_ext}"
    file_path = FOOTERS_DIR / filename
    
    # Salva il file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante il salvataggio del file: {str(e)}"
        )
    
    # Aggiorna il template con il path del footer
    relative_path = f"/data/templates/footers/{filename}"
    update_data = DocumentTemplateUpdate(footer_path=relative_path)
    updated_template = DocumentTemplateService.update(db, template_id, update_data)
    
    return updated_template


@router.delete("/{template_id}/delete-logo", response_model=DocumentTemplate)
def delete_logo(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Rimuove il logo da un template"""
    template = DocumentTemplateService.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} non trovato"
        )
    
    # Elimina il file se esiste
    if template.logo_path:
        file_path = Path("/app") / template.logo_path.lstrip("/")
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                # Log error but continue
                logger.warning(f"Errore eliminazione file logo: {e}")
    
    # Aggiorna il template
    update_data = DocumentTemplateUpdate(logo_path=None)
    updated_template = DocumentTemplateService.update(db, template_id, update_data)
    
    return updated_template


@router.delete("/{template_id}/delete-footer", response_model=DocumentTemplate)
def delete_footer(template_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_admin)):
    """Rimuove il footer da un template"""
    template = DocumentTemplateService.get_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} non trovato"
        )
    
    # Elimina il file se esiste
    if template.footer_path:
        file_path = Path("/app") / template.footer_path.lstrip("/")
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                # Log error but continue
                logger.warning(f"Errore eliminazione file footer: {e}")
    
    # Aggiorna il template
    update_data = DocumentTemplateUpdate(footer_path=None)
    updated_template = DocumentTemplateService.update(db, template_id, update_data)
    
    return updated_template
