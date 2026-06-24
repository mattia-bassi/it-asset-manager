from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.models.asset import Asset
from app.models.asset_type import AssetType
from app.models.site import Site
from app.models.person import Person
from app.models.location import Location
from app.models.supplier import Supplier
from app.schemas.asset import AssetCreate, AssetUpdate
from app.services.audit_service import AuditService

import logging

logger = logging.getLogger(__name__)


class AssetService:
    """Service per la gestione degli asset."""

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        asset_type_id: Optional[int] = None,
        site_id: Optional[int] = None,
        person_id: Optional[int] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[list[dict], int]:
        """
        Recupera tutti gli asset con filtri opzionali.
        Ritorna (lista_asset_con_dettagli, totale)
        """
        query = select(
            Asset,
            AssetType.name.label('asset_type_name'),
            Site.name.label('site_name'),
            func.concat(Person.first_name, ' ', Person.last_name).label('person_name'),
            Location.name.label('location_name'),
            Supplier.name.label('supplier_name')
        ).outerjoin(AssetType, Asset.asset_type_id == AssetType.id
        ).outerjoin(Site, Asset.site_id == Site.id
        ).outerjoin(Person, Asset.person_id == Person.id
        ).outerjoin(Location, Asset.location_id == Location.id
        ).outerjoin(Supplier, Asset.supplier_id == Supplier.id)
        
        # Filtri
        if is_active is not None:
            query = query.where(Asset.is_active == is_active)
        
        if asset_type_id is not None:
            query = query.where(Asset.asset_type_id == asset_type_id)
        
        if site_id is not None:
            query = query.where(Asset.site_id == site_id)
        
        if person_id is not None:
            query = query.where(Asset.person_id == person_id)
        
        if status is not None:
            query = query.where(Asset.status == status)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Asset.asset_code.ilike(search_term),
                    Asset.serial_number.ilike(search_term),
                    Asset.manufacturer.ilike(search_term),
                    Asset.model.ilike(search_term),
                    Asset.mac_address.ilike(search_term)
                )
            )
        
        # Conta totale
        total = db.scalar(select(func.count()).select_from(query.subquery()))
        
        # Paginazione e ordinamento
        query = query.order_by(Asset.manufacturer, Asset.model).offset(skip).limit(limit)
        results = db.execute(query).all()
        
        # Converti in dizionari
        assets_with_details = []
        for asset, type_name, site_name, person_name, location_name, supplier_name in results:
            asset_dict = {
                "id": asset.id,
                "asset_code": asset.asset_code,
                "serial_number": asset.serial_number,
                "mac_address": asset.mac_address,
                "asset_type_id": asset.asset_type_id,
                "manufacturer": asset.manufacturer,
                "model": asset.model,
                "site_id": asset.site_id,
                "person_id": asset.person_id,
                "status": asset.status,
                "purchase_date": asset.purchase_date,
                "warranty_expiry": asset.warranty_expiry,
                "specifications": asset.specifications,
                "notes": asset.notes,
                "qr_code": asset.qr_code,
                "is_active": asset.is_active,
                "created_at": asset.created_at,
                "updated_at": asset.updated_at,
                "asset_type_name": type_name,
                "site_name": site_name,
                "person_name": person_name,
                "location_name": location_name,
                "supplier_id": asset.supplier_id,
                "supplier_name": supplier_name
            }
            assets_with_details.append(asset_dict)
        
        return assets_with_details, total or 0

    @staticmethod
    def get_by_id(db: Session, asset_id: int) -> Optional[Asset]:
        """Recupera un asset per ID."""
        return db.scalar(select(Asset).where(Asset.id == asset_id))

    @staticmethod
    def get_by_serial(db: Session, serial_number: str) -> Optional[Asset]:
        """Recupera un asset per numero seriale."""
        return db.scalar(select(Asset).where(Asset.serial_number == serial_number))

    @staticmethod
    def create(db: Session, asset_data: AssetCreate) -> Asset:
        """Crea un nuovo asset."""
        # Verifica duplicati seriale
        existing = AssetService.get_by_serial(db, asset_data.serial_number)
        if existing:
            raise ValueError(f"Esiste già un asset con seriale '{asset_data.serial_number}'")
        
        # Verifica duplicati asset_code se presente
        if asset_data.asset_code:
            existing_code = db.scalar(select(Asset).where(Asset.asset_code == asset_data.asset_code))
            if existing_code:
                raise ValueError(f"Esiste già un asset con codice '{asset_data.asset_code}'")
        
        # Converti model_dump e gestisci stringhe vuote -> NULL
        data = asset_data.model_dump()
        # FIX: Converti stringa vuota in None per campi unique nullable
        if 'asset_code' in data and data['asset_code'] == '':
            data['asset_code'] = None
        if 'mac_address' in data and data['mac_address'] == '':
            data['mac_address'] = None

        asset = Asset(**data)
        db.add(asset)
        db.commit()
        db.refresh(asset)

        # Audit log
        try:
            AuditService.log_action(
                db=db,
                action="CREATE",
                entity_type="asset",
                entity_id=asset.id,
                details=f"Creato asset {asset.manufacturer} {asset.model} - SN: {asset.serial_number}",
                new_value={
                    "manufacturer": asset.manufacturer,
                    "model": asset.model,
                    "serial_number": asset.serial_number,
                    "status": asset.status
                }
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        return asset

    @staticmethod
    def update(db: Session, asset_id: int, asset_data: AssetUpdate) -> Optional[Asset]:
        """Aggiorna un asset esistente."""
        asset = AssetService.get_by_id(db, asset_id)
        if not asset:
            return None

        # Salva old values per audit
        old_value = {
            "manufacturer": asset.manufacturer,
            "model": asset.model,
            "serial_number": asset.serial_number,
            "status": asset.status,
            "person_id": asset.person_id,
            "site_id": asset.site_id
        }

        # Validazione: stati non operativi richiedono asset non assegnato
        NON_OPERATIONAL_STATUSES = ['manutenzione', 'riparazione', 'dismesso']
        
        # Se si sta cambiando status
        if asset_data.status and asset_data.status != asset.status:
            # E il nuovo status è non operativo
            if asset_data.status in NON_OPERATIONAL_STATUSES:
                # Verifica che asset non sia assegnato
                if asset.person_id is not None:
                    # Ottieni nome persona per messaggio chiaro
                    from app.models.person import Person
                    person = db.query(Person).filter(Person.id == asset.person_id).first()
                    person_name = f"{person.first_name} {person.last_name}" if person else "utente"
                    
                    raise ValueError(
                        f"Impossibile cambiare stato a '{asset_data.status}': "
                        f"l'asset è attualmente assegnato a {person_name}. "
                        f"Prima registra la restituzione dell'asset."
                    )
        
        # Validazione: se si sta assegnando l'asset (person_id), verificare status operativo
        if asset_data.person_id is not None and asset_data.person_id != asset.person_id:
            # Si sta cercando di assegnare l'asset
            current_status = asset_data.status if asset_data.status else asset.status
            
            if current_status in NON_OPERATIONAL_STATUSES:
                raise ValueError(
                    f"Impossibile assegnare l'asset: "
                    f"lo stato attuale è '{current_status}'. "
                    f"Prima cambia lo stato a 'disponibile' o 'deposito'."
                )
        
        # Verifica duplicati seriale se modificato
        if asset_data.serial_number and asset_data.serial_number != asset.serial_number:
            existing = AssetService.get_by_serial(db, asset_data.serial_number)
            if existing and existing.id != asset_id:
                raise ValueError(f"Esiste già un asset con seriale '{asset_data.serial_number}'")
        
        # Verifica duplicati asset_code se modificato
        if asset_data.asset_code and asset_data.asset_code != asset.asset_code:
            existing_code = db.scalar(select(Asset).where(Asset.asset_code == asset_data.asset_code))
            if existing_code and existing_code.id != asset_id:
                raise ValueError(f"Esiste già un asset con codice '{asset_data.asset_code}'")

        update_data = asset_data.model_dump(exclude_unset=True)
        # FIX: Converti stringa vuota in None per campi unique nullable
        if 'asset_code' in update_data and update_data['asset_code'] == '':
            update_data['asset_code'] = None
        if 'mac_address' in update_data and update_data['mac_address'] == '':
            update_data['mac_address'] = None
        
        for field, value in update_data.items():
            setattr(asset, field, value)
        
        db.commit()

        # Audit log
        try:
            new_value = {
                "manufacturer": asset.manufacturer,
                "model": asset.model,
                "serial_number": asset.serial_number,
                "status": asset.status,
                "person_id": asset.person_id,
                "site_id": asset.site_id
            }
            AuditService.log_action(
                db=db,
                action="UPDATE",
                entity_type="asset",
                entity_id=asset.id,
                details=f"Aggiornato asset {asset.manufacturer} {asset.model}",
                old_value=old_value,
                new_value=new_value
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        db.refresh(asset)
        return asset

    @staticmethod
    def delete(db: Session, asset_id: int) -> bool:
        """Disattiva un asset (soft delete)."""
        asset = AssetService.get_by_id(db, asset_id)
        if not asset:
            return False

        # Salva old status per audit
        old_status = asset.status

        asset.is_active = False
        asset.status = "dismesso"
        db.commit()

        # Audit log
        try:
            AuditService.log_action(
                db=db,
                action="DELETE",
                entity_type="asset",
                entity_id=asset.id,
                details=f"Asset disattivato (soft delete): {asset.manufacturer} {asset.model}",
                old_value={"is_active": True, "status": old_status}
            )
        except Exception as e:
            logger.warning("Audit log failed: %s", e)

        return True

    @staticmethod
    def hard_delete(db: Session, asset_id: int) -> bool:
        """Elimina definitivamente un asset."""
        asset = AssetService.get_by_id(db, asset_id)
        if not asset:
            return False
        
        db.delete(asset)
        db.commit()
        return True

