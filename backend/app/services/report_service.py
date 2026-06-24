from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Optional
from datetime import date, datetime
from app.models.asset import Asset
from app.models.assignment import Assignment
from app.models.assignment_item import AssignmentItem
from app.models.inventory_sku import InventorySku
from app.models.person import Person
from app.models.site import Site
from app.models.asset_type import AssetType


class ReportService:
    """Servizio per generare dati dei report"""
    
    @classmethod
    def get_assets_by_type(
        cls,
        db: Session,
        site_id: Optional[int] = None,
        is_active: bool = True
    ) -> List[Dict]:
        """
        Report 1: Conteggio asset per tipo
        Raggruppa asset per tipo e conta totale, assegnati, disponibili, guasti
        """
        query = db.query(
            AssetType.name.label('tipo'),
            func.count(Asset.id).label('totale'),
            func.sum(
                func.IF(Asset.status == 'assegnato', 1, 0)
            ).label('assegnati'),
            func.sum(
                func.IF(Asset.status == 'disponibile', 1, 0)
            ).label('disponibili'),
            func.sum(
                func.IF(Asset.status == 'guasto', 1, 0)
            ).label('guasti')
        ).join(
            AssetType, Asset.asset_type_id == AssetType.id
        ).filter(
            Asset.is_active == is_active
        )
        
        if site_id:
            query = query.filter(Asset.site_id == site_id)
        
        query = query.group_by(AssetType.name).order_by(AssetType.name)
        
        results = []
        for row in query.all():
            results.append({
                'tipo': row.tipo,
                'totale': int(row.totale or 0),
                'assegnati': int(row.assegnati or 0),
                'disponibili': int(row.disponibili or 0),
                'guasti': int(row.guasti or 0)
            })
        
        return results
    
    @classmethod
    def get_faulty_assets(
        cls,
        db: Session,
        site_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Report 2: Lista asset guasti
        Raggruppa per marca/modello e conta frequenza guasti
        """
        query = db.query(
            Asset.manufacturer.label('marca'),
            Asset.model.label('modello'),
            AssetType.name.label('tipo'),
            func.count(Asset.id).label('numero_guasti')
        ).join(
            AssetType, Asset.asset_type_id == AssetType.id
        ).filter(
            Asset.status == 'guasto',
            Asset.is_active == True
        )
        
        if site_id:
            query = query.filter(Asset.site_id == site_id)
        
        query = query.group_by(
            Asset.manufacturer,
            Asset.model,
            AssetType.name
        ).order_by(
            func.count(Asset.id).desc()
        )
        
        results = []
        for row in query.all():
            results.append({
                'marca': row.marca,
                'modello': row.modello,
                'tipo': row.tipo,
                'numero_guasti': int(row.numero_guasti)
            })
        
        return results
    
    @classmethod
    def get_active_assignments(
        cls,
        db: Session,
        site_id: Optional[int] = None,
        person_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Report 3: Assegnazioni attive
        Lista completa con persona, sede, materiali
        """
        query = db.query(
            Assignment.id,
            Assignment.assignment_date,
            Person.first_name,
            Person.last_name,
            Person.email,
            Site.name.label('sede'),
            func.count(AssignmentItem.id).label('num_items')
        ).join(
            Person, Assignment.person_id == Person.id
        ).outerjoin(
            Site, Person.site_id == Site.id
        ).join(
            AssignmentItem, Assignment.id == AssignmentItem.assignment_id
        ).filter(
            Assignment.status == 'attivo',
            Assignment.return_date.is_(None)
        )
        
        if site_id:
            query = query.filter(Person.site_id == site_id)
        
        if person_id:
            query = query.filter(Assignment.person_id == person_id)
        
        query = query.group_by(
            Assignment.id
        ).order_by(
            Assignment.assignment_date.desc()
        )
        
        results = []
        for row in query.all():
            results.append({
                'numero_assegnazione': f"ASS-{row.assignment_date.year}-{row.id:03d}" if row.assignment_date else f"ASS-{row.id:03d}",
                'data': row.assignment_date.strftime('%d/%m/%Y'),
                'persona': f"{row.first_name} {row.last_name}",
                'email': row.email or '',
                'sede': row.sede or '',
                'num_items': int(row.num_items)
            })
        
        return results
    
    @classmethod
    def get_assignment_history(
        cls,
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        person_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Report 4: Storico assegnazioni
        Tutte le assegnazioni con durata
        """
        query = db.query(
            Assignment.id,
            Assignment.assignment_date,
            Assignment.return_date,
            Assignment.status,
            Person.first_name,
            Person.last_name,
            Site.name.label('sede'),
            func.count(AssignmentItem.id).label('num_items')
        ).join(
            Person, Assignment.person_id == Person.id
        ).outerjoin(
            Site, Person.site_id == Site.id
        ).join(
            AssignmentItem, Assignment.id == AssignmentItem.assignment_id
        )
        
        if start_date:
            query = query.filter(Assignment.assignment_date >= start_date)
        
        if end_date:
            query = query.filter(Assignment.assignment_date <= end_date)
        
        if person_id:
            query = query.filter(Assignment.person_id == person_id)
        
        query = query.group_by(
            Assignment.id
        ).order_by(
            Assignment.assignment_date.desc()
        )
        
        results = []
        for row in query.all():
            # Calcola durata
            if row.return_date:
                durata = (row.return_date - row.assignment_date).days
            else:
                durata = (date.today() - row.assignment_date).days
            
            results.append({
                'numero_assegnazione': f"ASS-{row.assignment_date.year}-{row.id:03d}" if row.assignment_date else f"ASS-{row.id:03d}",
                'data_assegnazione': row.assignment_date.strftime('%d/%m/%Y'),
                'data_riconsegna': row.return_date.strftime('%d/%m/%Y') if row.return_date else 'Attiva',
                'durata_giorni': durata,
                'stato': row.status,
                'persona': f"{row.first_name} {row.last_name}",
                'sede': row.sede or '',
                'num_items': int(row.num_items)
            })
        
        return results
    
    @classmethod
    def get_low_stock_inventory(
        cls,
        db: Session,
        threshold_percentage: int = 100
    ) -> List[Dict]:
        """
        Report 5: Inventario sotto soglia
        Materiali con quantità <= min_quantity * (threshold_percentage/100)
        """
        query = db.query(
            InventorySku.category,
            InventorySku.device,
            InventorySku.brand,
            InventorySku.quantity,
            InventorySku.min_quantity
        ).filter(
            InventorySku.is_active == True,
            InventorySku.quantity <= (InventorySku.min_quantity * threshold_percentage / 100)
        ).order_by(
            InventorySku.quantity.asc()
        )
        
        results = []
        for row in query.all():
            percentuale = (row.quantity / row.min_quantity * 100) if row.min_quantity > 0 else 0
            
            results.append({
                'categoria': row.category,
                'dispositivo': row.device,
                'marca': row.brand or '',
                'quantita_attuale': row.quantity,
                'quantita_minima': row.min_quantity,
                'percentuale': round(percentuale, 1),
                'stato_alert': 'CRITICO' if percentuale < 50 else 'BASSO'
            })
        
        return results
    
    @classmethod
    def get_assets_by_site(
        cls,
        db: Session,
        is_active: bool = True
    ) -> List[Dict]:
        """
        Report 6: Asset per sede
        Distribuzione e conteggio per ubicazione
        """
        query = db.query(
            Site.name.label('sede'),
            AssetType.name.label('tipo'),
            func.count(Asset.id).label('totale')
        ).join(
            Site, Asset.site_id == Site.id
        ).join(
            AssetType, Asset.asset_type_id == AssetType.id
        ).filter(
            Asset.is_active == is_active,
            Site.is_active == True
        ).group_by(
            Site.name,
            AssetType.name
        ).order_by(
            Site.name,
            AssetType.name
        )
        
        results = []
        for row in query.all():
            results.append({
                'sede': row.sede,
                'tipo': row.tipo,
                'totale': int(row.totale)
            })
        
        return results

    @classmethod
    def get_my_assets(
        cls,
        db: Session,
        person_id: int
    ) -> List[Dict]:
        """
        Report USER: I miei asset attualmente assegnati
        Lista asset attivi assegnati alla persona
        """
        query = db.query(
            Asset.asset_code,
            Asset.manufacturer,
            Asset.model,
            Asset.serial_number,
            AssetType.name.label('tipo'),
            Assignment.assignment_number,
            Assignment.assignment_date,
            Site.name.label('sede')
        ).join(
            AssetType, Asset.asset_type_id == AssetType.id
        ).join(
            AssignmentItem, AssignmentItem.asset_id == Asset.id
        ).join(
            Assignment, AssignmentItem.assignment_id == Assignment.id
        ).outerjoin(
            Site, Asset.site_id == Site.id
        ).filter(
            Assignment.person_id == person_id,
            Assignment.status == 'attivo',
            Assignment.is_active == True,
            Asset.is_active == True
        ).order_by(
            Assignment.assignment_date.desc()
        )

        results = []
        for row in query.all():
            results.append({
                'asset_code': row.asset_code,
                'tipo': row.tipo,
                'marca': row.manufacturer or '',
                'modello': row.model or '',
                'seriale': row.serial_number or '',
                'sede': row.sede or '',
                'numero_assegnazione': row.assignment_number,
                'data_assegnazione': row.assignment_date.strftime('%d/%m/%Y')
            })

        return results

    @classmethod
    def get_my_assignments(
        cls,
        db: Session,
        person_id: int
    ) -> List[Dict]:
        """
        Report USER: Storico delle mie assegnazioni
        Tutte le assegnazioni (attive e completate) della persona
        """
        query = db.query(
            Assignment.id,
            Assignment.assignment_date,
            Assignment.return_date,
            Assignment.status,
            Assignment.assignment_type,
            Site.name.label('sede'),
            func.count(AssignmentItem.id).label('num_items')
        ).outerjoin(
            Person, Assignment.person_id == Person.id
        ).outerjoin(
            Site, Person.site_id == Site.id
        ).join(
            AssignmentItem, Assignment.id == AssignmentItem.assignment_id
        ).filter(
            Assignment.person_id == person_id,
            Assignment.status == 'attivo'
        ).group_by(
            Assignment.id
        ).order_by(
            Assignment.assignment_date.desc()
        )

        results = []
        for row in query.all():
            # Calcola durata
            if row.return_date:
                durata = (row.return_date - row.assignment_date).days
            else:
                durata = (date.today() - row.assignment_date).days

            results.append({
                'numero_assegnazione': f"ASS-{row.assignment_date.year}-{row.id:03d}",
                'tipo_assegnazione': row.assignment_type or 'nuova',
                'data_assegnazione': row.assignment_date.strftime('%d/%m/%Y'),
                'data_riconsegna': row.return_date.strftime('%d/%m/%Y') if row.return_date else 'Attiva',
                'durata_giorni': durata,
                'stato': row.status,
                'sede': row.sede or '',
                'num_materiali': int(row.num_items)
            })

        return results
