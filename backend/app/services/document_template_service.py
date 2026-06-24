from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.document_template import DocumentTemplate
from app.schemas.document_template import DocumentTemplateCreate, DocumentTemplateUpdate


class DocumentTemplateService:
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[DocumentTemplate]:
        """Recupera tutti i template"""
        query = db.query(DocumentTemplate)
        if active_only:
            query = query.filter(DocumentTemplate.is_active == True)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, template_id: int) -> Optional[DocumentTemplate]:
        """Recupera un template per ID"""
        return db.query(DocumentTemplate).filter(DocumentTemplate.id == template_id).first()

    @staticmethod
    def get_default(db: Session) -> Optional[DocumentTemplate]:
        """Recupera il template predefinito"""
        return db.query(DocumentTemplate).filter(
            and_(
                DocumentTemplate.is_default == True,
                DocumentTemplate.is_active == True
            )
        ).first()

    @staticmethod
    def create(db: Session, template: DocumentTemplateCreate) -> DocumentTemplate:
        """Crea un nuovo template"""
        # Se il nuovo template è default, rimuovi il flag dagli altri
        if template.is_default:
            db.query(DocumentTemplate).filter(DocumentTemplate.is_default == True).update(
                {"is_default": False}
            )
        
        db_template = DocumentTemplate(**template.model_dump())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template

    @staticmethod
    def update(db: Session, template_id: int, template: DocumentTemplateUpdate) -> Optional[DocumentTemplate]:
        """Aggiorna un template esistente"""
        db_template = DocumentTemplateService.get_by_id(db, template_id)
        if not db_template:
            return None

        # Se il template viene impostato come default, rimuovi il flag dagli altri
        if template.is_default and not db_template.is_default:
            db.query(DocumentTemplate).filter(
                and_(
                    DocumentTemplate.id != template_id,
                    DocumentTemplate.is_default == True
                )
            ).update({"is_default": False})

        update_data = template.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_template, field, value)

        db.commit()
        db.refresh(db_template)
        return db_template

    @staticmethod
    def delete(db: Session, template_id: int) -> bool:
        """Soft delete di un template"""
        db_template = DocumentTemplateService.get_by_id(db, template_id)
        if not db_template:
            return False

        # Non permettere eliminazione del template default
        if db_template.is_default:
            return False

        db_template.is_active = False
        db.commit()
        return True

    @staticmethod
    def set_default(db: Session, template_id: int) -> Optional[DocumentTemplate]:
        """Imposta un template come predefinito"""
        db_template = DocumentTemplateService.get_by_id(db, template_id)
        if not db_template or not db_template.is_active:
            return None

        # Rimuovi default dagli altri
        db.query(DocumentTemplate).filter(DocumentTemplate.is_default == True).update(
            {"is_default": False}
        )

        db_template.is_default = True
        db.commit()
        db.refresh(db_template)
        return db_template
