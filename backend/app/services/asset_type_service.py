from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.asset_type import AssetType
from app.schemas.asset_type import AssetTypeCreate, AssetTypeUpdate


class AssetTypeService:
    """Service per la gestione dei tipi di asset."""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        parent_id: Optional[int] = None
    ) -> tuple[list[dict], int]:
        """
        Recupera tutti i tipi di asset con filtri opzionali.
        Ritorna (lista_tipi_con_padre, totale)
        """
        # Query con join per ottenere il nome del padre
        from sqlalchemy.orm import aliased
        ParentType = aliased(AssetType)
        
        query = select(AssetType, ParentType.name.label('parent_name')).outerjoin(
            ParentType, AssetType.parent_id == ParentType.id
        )
        
        # Filtro attivo/inattivo
        if is_active is not None:
            query = query.where(AssetType.is_active == is_active)
        
        # Filtro per tipo padre
        if parent_id is not None:
            query = query.where(AssetType.parent_id == parent_id)
        
        # Conta totale
        count_query = select(AssetType)
        if is_active is not None:
            count_query = count_query.where(AssetType.is_active == is_active)
        if parent_id is not None:
            count_query = count_query.where(AssetType.parent_id == parent_id)
        total = db.scalar(select(func.count()).select_from(count_query.subquery()))
        
        # Paginazione e ordinamento
        query = query.order_by(AssetType.name).offset(skip).limit(limit)
        results = db.execute(query).all()
        
        # Converti in dizionari
        types_with_parent = []
        for asset_type, parent_name in results:
            type_dict = {
                "id": asset_type.id,
                "name": asset_type.name,
                "parent_id": asset_type.parent_id,
                "description": asset_type.description,
                "fields_schema": asset_type.fields_schema,
                "is_active": asset_type.is_active,
                "created_at": asset_type.created_at,
                "updated_at": asset_type.updated_at,
                "parent_name": parent_name
            }
            types_with_parent.append(type_dict)
        
        return types_with_parent, total or 0

    @staticmethod
    def get_by_id(db: Session, type_id: int) -> Optional[AssetType]:
        """Recupera un tipo per ID."""
        return db.scalar(select(AssetType).where(AssetType.id == type_id))

    @staticmethod
    def get_hierarchy(db: Session) -> list[dict]:
        """
        Recupera la gerarchia completa dei tipi in formato ad albero.
        """
        all_types = db.scalars(select(AssetType).where(AssetType.is_active == True).order_by(AssetType.name)).all()
        
        # Crea dizionario per lookup veloce
        types_dict = {t.id: {
            "id": t.id,
            "name": t.name,
            "parent_id": t.parent_id,
            "description": t.description,
            "fields_schema": t.fields_schema,
            "children": []
        } for t in all_types}
        
        # Costruisci albero
        root_types = []
        for type_id, type_data in types_dict.items():
            if type_data["parent_id"] is None:
                root_types.append(type_data)
            else:
                parent = types_dict.get(type_data["parent_id"])
                if parent:
                    parent["children"].append(type_data)
        
        return root_types

    @staticmethod
    def create(db: Session, type_data: AssetTypeCreate) -> AssetType:
        """Crea un nuovo tipo di asset."""
        asset_type = AssetType(**type_data.model_dump())
        db.add(asset_type)
        db.commit()
        db.refresh(asset_type)
        return asset_type

    @staticmethod
    def update(db: Session, type_id: int, type_data: AssetTypeUpdate) -> Optional[AssetType]:
        """Aggiorna un tipo esistente."""
        asset_type = AssetTypeService.get_by_id(db, type_id)
        if not asset_type:
            return None
        
        update_data = type_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(asset_type, field, value)
        
        db.commit()
        db.refresh(asset_type)
        return asset_type

    @staticmethod
    def delete(db: Session, type_id: int) -> bool:
        """Disattiva un tipo (soft delete)."""
        asset_type = AssetTypeService.get_by_id(db, type_id)
        if not asset_type:
            return False
        
        asset_type.is_active = False
        db.commit()
        return True

