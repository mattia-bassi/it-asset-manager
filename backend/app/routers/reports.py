from fastapi import APIRouter, Depends, Query, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import case, func
from typing import Optional
from datetime import date, datetime
from pathlib import Path
import logging

from app.api.deps import get_db, get_current_user
from app.core.cors import get_cors_headers
from app.models.user import User
from app.models.person import Person
from app.services.report_service import ReportService
from app.services.excel_generator_service import ExcelGeneratorService
from app.services.document_template_service import DocumentTemplateService

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/assets-by-type/excel")
def get_assets_by_type_excel(
    site_id: Optional[int] = Query(None, description="Filtra per sede"),
    is_active: bool = Query(True, description="Solo asset attivi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report 1: Asset per Tipo (Excel)"""
    # Recupera dati
    data = ReportService.get_assets_by_type(db, site_id, is_active)
    
    # Recupera logo dal template
    template = DocumentTemplateService.get_default(db)
    logo_path = None
    if template and template.logo_path:
        logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
    
    # Genera Excel
    file_path = ExcelGeneratorService.generate_assets_by_type_report(data, logo_path)
    full_path = Path("/app") / file_path.lstrip("/")
    
    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/faulty-assets/excel")
def get_faulty_assets_excel(
    site_id: Optional[int] = Query(None, description="Filtra per sede"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report 2: Dispositivi Guasti (Excel)"""
    data = ReportService.get_faulty_assets(db, site_id)
    
    template = DocumentTemplateService.get_default(db)
    logo_path = None
    if template and template.logo_path:
        logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
    
    file_path = ExcelGeneratorService.generate_faulty_assets_report(data, logo_path)
    full_path = Path("/app") / file_path.lstrip("/")
    
    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/active-assignments/excel")
def get_active_assignments_excel(
    site_id: Optional[int] = Query(None, description="Filtra per sede"),
    person_id: Optional[int] = Query(None, description="Filtra per persona"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report 3: Assegnazioni Attive (Excel)"""
    data = ReportService.get_active_assignments(db, site_id, person_id)
    
    template = DocumentTemplateService.get_default(db)
    logo_path = None
    if template and template.logo_path:
        logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
    
    file_path = ExcelGeneratorService.generate_active_assignments_report(data, logo_path)
    full_path = Path("/app") / file_path.lstrip("/")
    
    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/assignment-history/excel")
def get_assignment_history_excel(
    request: Request,
    start_date: Optional[date] = Query(None, description="Data inizio"),
    end_date: Optional[date] = Query(None, description="Data fine"),
    person_id: Optional[int] = Query(None, description="Filtra per persona"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report 4: Storico Assegnazioni (Excel)"""
    try:
        data = ReportService.get_assignment_history(db, start_date, end_date, person_id)
        template = DocumentTemplateService.get_default(db)
        logo_path = None
        if template and template.logo_path:
            logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
        file_path = ExcelGeneratorService.generate_assignment_history_report(data, logo_path)
        full_path = Path("/app") / file_path.lstrip("/")
        return FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        logger.exception("Errore report assignment-history: %s", e)
        return JSONResponse(
            status_code=500,
            content={"detail": str(e) or "Errore generazione report"},
            headers=get_cors_headers(request),
        )


@router.get("/low-stock/excel")
def get_low_stock_excel(
    threshold: int = Query(100, description="Percentuale soglia (default 100%)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report 5: Inventario Sotto Soglia (Excel)"""
    data = ReportService.get_low_stock_inventory(db, threshold)
    
    template = DocumentTemplateService.get_default(db)
    logo_path = None
    if template and template.logo_path:
        logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
    
    file_path = ExcelGeneratorService.generate_low_stock_report(data, logo_path)
    full_path = Path("/app") / file_path.lstrip("/")
    
    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/assets-by-site/excel")
def get_assets_by_site_excel(
    is_active: bool = Query(True, description="Solo asset attivi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report 6: Asset per Sede (Excel)"""
    data = ReportService.get_assets_by_site(db, is_active)
    
    template = DocumentTemplateService.get_default(db)
    logo_path = None
    if template and template.logo_path:
        logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
    
    file_path = ExcelGeneratorService.generate_assets_by_site_report(data, logo_path)
    full_path = Path("/app") / file_path.lstrip("/")
    
    return FileResponse(
        path=str(full_path),
        filename=full_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/sims-by-operator/excel")
async def get_sims_by_operator_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report SIM raggruppate per operatore"""
    from app.models.sim import Sim
    
    # Query SIM raggruppate per operatore
    sims_query = db.query(
        Sim.operatore,
        func.count(Sim.id).label('totale'),
        func.sum(case((Sim.status == 'disponibile', 1), else_=0)).label('disponibili'),
        func.sum(case((Sim.status == 'assegnata', 1), else_=0)).label('assegnate'),
        func.sum(case((Sim.status == 'disattivata', 1), else_=0)).label('disattivate')
    ).group_by(Sim.operatore).order_by(Sim.operatore).all()
    
    data = []
    for row in sims_query:
        data.append({
            'Operatore': row.operatore,
            'Totale SIM': row.totale,
            'Disponibili': row.disponibili or 0,
            'Assegnate': row.assegnate or 0,
            'Disattivate': getattr(row, 'disattivate', 0) or 0
        })
    
    # Recupera logo dal template
    template = DocumentTemplateService.get_default(db)
    logo_path = None
    if template and template.logo_path:
        logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
    
    # Genera Excel
    filename = ExcelGeneratorService.generate_report(
        title="REPORT SIM PER OPERATORE",
        data=data,
        logo_path=logo_path
    )
    
    # Il metodo generate_report restituisce già il path completo
    return FileResponse(
        path=filename,
        filename=f"report_sim_operatore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/sims-by-status/excel")
async def get_sims_by_status_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report SIM raggruppate per status"""
    from app.models.sim import Sim
    
    # Query tutte le SIM
    sims = db.query(Sim).order_by(Sim.status, Sim.operatore).all()
    
    data = []
    for sim in sims:
        data.append({
            'Seriale': sim.seriale,
            'Operatore': sim.operatore,
            'Numero Telefono': sim.numero_telefono,
            'Status': sim.status,
            'Data Creazione': sim.created_at.strftime('%d/%m/%Y') if sim.created_at else ''
        })
    
    # Recupera logo dal template
    template = DocumentTemplateService.get_default(db)
    logo_path = None
    if template and template.logo_path:
        logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
    
    # Genera Excel
    filename = ExcelGeneratorService.generate_report(
        title="REPORT SIM PER STATUS",
        data=data,
        logo_path=logo_path
    )
    
    # Il metodo generate_report restituisce già il path completo
    return FileResponse(
        path=filename,
        filename=f"report_sim_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/sims-detailed/excel")
async def get_sims_detailed_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report SIM dettagliato con info persone assegnate"""
    from app.models.sim import Sim
    
    # Query SIM con join su persone
    sims = db.query(Sim).outerjoin(
        Person, 
        Person.mobile_phone == Sim.numero_telefono
    ).order_by(Sim.operatore, Sim.status).all()
    
    data = []
    for sim in sims:
        # Trova persona associata
        person = db.query(Person).filter(Person.mobile_phone == sim.numero_telefono).first()
        
        data.append({
            'Seriale': sim.seriale,
            'Operatore': sim.operatore,
            'Numero': sim.numero_telefono,
            'Status': sim.status,
            'Assegnata A': f"{person.first_name} {person.last_name}" if person else '-',
            'Email': person.email if person else '-',
            'Sede': person.site.name if person and person.site else '-',
            'Data Creazione': sim.created_at.strftime('%d/%m/%Y') if sim.created_at else ''
        })
    
    # Recupera logo dal template
    template = DocumentTemplateService.get_default(db)
    logo_path = None
    if template and template.logo_path:
        logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
    
    # Genera Excel
    filename = ExcelGeneratorService.generate_report(
        title="REPORT SIM DETTAGLIATO",
        data=data,
        logo_path=logo_path
    )
    
    # Il metodo generate_report restituisce già il path completo
    return FileResponse(
        path=filename,
        filename=f"report_sim_dettagliato_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/my-assets/excel")
async def get_my_assets_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report USER: I miei asset attualmente assegnati"""
    if not current_user.person_id:
        raise HTTPException(status_code=400, detail="Utente non associato a una persona")
    
    # Recupera dati dal ReportService
    data = ReportService.get_my_assets(db, current_user.person_id)
    
    # Recupera logo dal template
    template = DocumentTemplateService.get_default(db)
    logo_path = None
    if template and template.logo_path:
        logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
    
    # Genera Excel
    filename = ExcelGeneratorService.generate_report(
        title="I MIEI ASSET",
        data=data,
        logo_path=logo_path
    )
    
    return FileResponse(
        path=filename,
        filename=f"my_assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@router.get("/my-assignments/excel")
async def get_my_assignments_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Report USER: Storico delle mie assegnazioni"""
    if not current_user.person_id:
        raise HTTPException(status_code=400, detail="Utente non associato a una persona")
    
    # Recupera dati dal ReportService
    data = ReportService.get_my_assignments(db, current_user.person_id)
    
    # Recupera logo dal template
    template = DocumentTemplateService.get_default(db)
    logo_path = None
    if template and template.logo_path:
        logo_path = str(Path("/app") / template.logo_path.lstrip("/"))
    
    # Genera Excel
    filename = ExcelGeneratorService.generate_report(
        title="STORICO MIE ASSEGNAZIONI",
        data=data,
        logo_path=logo_path
    )
    
    return FileResponse(
        path=filename,
        filename=f"my_assignments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
