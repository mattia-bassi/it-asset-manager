import logging
import os
import re
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from app.models.document import Document
from app.models.user import User
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

DOCUMENTS_DIR = "/app/data/documents/"


def _doc_to_dict(doc: Document) -> dict:
    """Converte model Document in dict compatibile con DocumentResponse."""
    return {
        "id": doc.id,
        "name": doc.name,
        "description": doc.description,
        "category": doc.category,
        "filename": doc.filename,
        "file_size": doc.file_size,
        "mime_type": doc.mime_type,
        "uploaded_by": doc.uploaded_by,
        "uploader_username": doc.uploader.username if doc.uploader else None,
        "is_active": doc.is_active,
        "created_at": doc.created_at,
    }


def get_all(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> dict:
    """
    Recupera tutti i documenti attivi con filtri opzionali.
    Ritorna dict con "items" e "total".
    """
    query = (
        select(Document)
        .where(Document.is_active == True)
        .options(joinedload(Document.uploader))
    )

    if category:
        query = query.where(Document.category == category)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Document.name.ilike(search_term)) | (Document.description.ilike(search_term))
        )

    total = db.scalar(select(func.count()).select_from(query.subquery()))

    query = query.order_by(Document.created_at.desc()).offset(skip).limit(limit)
    results = db.execute(query).unique().scalars().all()

    items = [_doc_to_dict(doc) for doc in results]
    return {"items": items, "total": total or 0}


def get_by_id(db: Session, document_id: int) -> Optional[Document]:
    """Recupera un documento per ID."""
    result = db.execute(
        select(Document)
        .where(Document.id == document_id)
        .options(joinedload(Document.uploader))
    )
    return result.unique().scalar_one_or_none()


def create(
    db: Session,
    name: str,
    description: Optional[str],
    category: str,
    filename: str,
    file_path: str,
    file_size: int,
    mime_type: str,
    uploaded_by: Optional[int],
    audit_user_id: Optional[int],
    audit_ip: Optional[str],
) -> dict:
    """Crea un record documento in DB e registra audit log."""
    doc = Document(
        name=name,
        description=description,
        category=category,
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        uploaded_by=uploaded_by,
        is_active=True,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        AuditService.log_action(
            db=db,
            action="CREATE",
            entity_type="document",
            entity_id=doc.id,
            user_id=audit_user_id,
            ip_address=audit_ip,
            details=f"Uploaded document: {name}",
        )
    except Exception as e:
        logger.error("Audit log failed: %s", e)

    return _doc_to_dict(doc)


def delete(
    db: Session,
    document_id: int,
    audit_user_id: Optional[int],
    audit_ip: Optional[str],
) -> bool:
    """Soft delete: imposta is_active=False. Non elimina il file fisico."""
    doc = get_by_id(db, document_id)
    if not doc:
        return False

    doc.is_active = False
    db.commit()

    try:
        AuditService.log_action(
            db=db,
            action="DELETE",
            entity_type="document",
            entity_id=document_id,
            user_id=audit_user_id,
            ip_address=audit_ip,
            details=f"Document soft deleted: {doc.name}",
        )
    except Exception as e:
        logger.error("Audit log failed: %s", e)

    return True


def save_file(file_content: bytes, filename: str) -> tuple[str, str, int]:
    """
    Salva il file in /app/data/documents/.
    Ritorna (unique_filename, file_path, file_size).
    """
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    safe_name = re.sub(r"[^\w\-.]", "_", os.path.basename(filename))
    unique_filename = f"{uuid4().hex[:8]}_{safe_name}"
    file_path = os.path.join(DOCUMENTS_DIR, unique_filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
    file_size = len(file_content)
    return unique_filename, file_path, file_size


def get_file_path(file_path: str) -> str:
    """Ritorna il path assoluto del file. Raise HTTPException 404 se non trovato."""
    abs_path = os.path.abspath(file_path)
    resolved = Path(abs_path).resolve()
    docs_root = Path(DOCUMENTS_DIR).resolve()
    if not resolved.is_relative_to(docs_root):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not resolved.exists():
        raise HTTPException(status_code=404, detail="File non trovato")
    return str(resolved)
