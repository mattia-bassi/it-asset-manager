from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, status, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.document import DocumentListResponse, DocumentResponse
from app.services import document_service

router = APIRouter()

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
    "text/plain",
]


@router.get("", response_model=DocumentListResponse)
def list_documents(
    skip: int = Query(0, ge=0, description="Numero di record da saltare"),
    limit: int = Query(100, ge=1, le=1000, description="Numero massimo di record"),
    category: Optional[str] = Query(None, description="Filtra per categoria"),
    search: Optional[str] = Query(None, description="Ricerca per nome o descrizione"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera la lista dei documenti con paginazione e filtri."""
    return document_service.get_all(
        db=db,
        skip=skip,
        limit=limit,
        category=category,
        search=search,
    )


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    category: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Carica un nuovo documento."""
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File troppo grande (max 20MB)",
        )

    mime_type = file.content_type or "application/octet-stream"
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo file non consentito",
        )

    unique_filename, file_path, file_size = document_service.save_file(content, file.filename or "unnamed")

    return document_service.create(
        db=db,
        name=name,
        description=description,
        category=category,
        filename=unique_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        uploaded_by=current_user.id,
        audit_user_id=current_user.id,
        audit_ip=request.client.host if request.client else None,
    )


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scarica il file del documento."""
    doc = document_service.get_by_id(db=db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} non trovato",
        )
    abs_path = document_service.get_file_path(doc.file_path)
    return FileResponse(
        path=abs_path,
        media_type=doc.mime_type,
        filename=doc.filename,
        headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'},
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recupera un documento per ID."""
    doc = document_service.get_by_id(db=db, document_id=document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} non trovato",
        )
    return document_service._doc_to_dict(doc)


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Elimina un documento (soft delete)."""
    success = document_service.delete(
        db=db,
        document_id=document_id,
        audit_user_id=current_user.id,
        audit_ip=request.client.host if request.client else None,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} non trovato",
        )
    return {"message": "Documento eliminato"}
