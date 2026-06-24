from fpdf import FPDF
from pathlib import Path
from datetime import date
from typing import Optional, List, Dict
import logging
import os

logger = logging.getLogger(__name__)

class AssignmentPDF(FPDF):
    """Classe PDF personalizzata per fogli di assegnazione"""

    def __init__(self, logo_path: Optional[str] = None, footer_path: Optional[str] = None):
        super().__init__()
        self.logo_path = logo_path
        self.footer_path = footer_path
        self.set_auto_page_break(auto=True, margin=55)  # 55mm per lasciare spazio al footer

    def header(self):
        """Header con logo a tutta larghezza"""
        if self.logo_path and Path(self.logo_path).exists():
            # Logo a tutta larghezza (A4 = 210mm, margini 10mm per lato = 190mm)
            self.image(self.logo_path, x=10, y=8, w=190)
        self.ln(30)

    def footer(self):
        """Footer con immagine a tutta larghezza e numero pagina"""
        self.set_y(-49)  # Footer inizia a 49mm dal fondo (20mm margine + 29mm footer)
        if self.footer_path and Path(self.footer_path).exists():
            # Footer a tutta larghezza
            self.image(self.footer_path, x=10, y=self.get_y(), w=190)
        self.set_y(-20)  # Numero pagina a 20mm dal fondo
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='C')


class PDFGeneratorService:
    """Servizio per generare PDF di assegnazione"""

    # Percorso base per i file
    BASE_PATH = Path("/app")
    OUTPUT_DIR = BASE_PATH / "data" / "documents"

    @classmethod
    def generate_assignment_pdf(
        cls,
        assignment_number: str,
        assignment_date: date,
        person_name: str,
        person_email: Optional[str],
        person_extension: Optional[str],  # NUOVO: Interno
        person_mobile_phone: Optional[str],  # NUOVO: Cellulare
        person_department: Optional[str],
        person_site: Optional[str],
        items: List[dict],
        password: Optional[str] = None,
        pin_sim: Optional[str] = None,
        pin_sblocco: Optional[str] = None,
        notes: Optional[str] = None,
        logo_path: Optional[str] = None,
        footer_path: Optional[str] = None,
    ) -> str:
        """
        Genera il PDF del foglio di assegnazione

        Returns:
            str: Percorso relativo del file PDF generato
        """
        # Assicura che la directory esista
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Risolvi percorsi logo e footer
        full_logo_path = None
        full_footer_path = None
        if logo_path:
            full_logo_path = str(cls.BASE_PATH / logo_path.lstrip("/"))
        if footer_path:
            full_footer_path = str(cls.BASE_PATH / footer_path.lstrip("/"))

        # Crea PDF
        pdf = AssignmentPDF(logo_path=full_logo_path, footer_path=full_footer_path)
        pdf.add_page()

        # Titolo
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(81, 93, 100)  # brand gray #515D64
        pdf.cell(0, 10, 'FOGLIO DI ASSEGNAZIONE MATERIALE', align='C', ln=True)
        pdf.ln(5)

        # Numero e data assegnazione
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, f'Assegnazione N.: {assignment_number}', ln=True)
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 8, f'Data: {assignment_date.strftime("%d/%m/%Y")}', ln=True)
        pdf.ln(5)

        # Dati dipendente
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(255, 221, 15)  # brand yellow #FFDD0F
        pdf.set_text_color(81, 93, 100)
        pdf.cell(0, 8, 'DATI DIPENDENTE', fill=True, ln=True)

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(52, 60, 64)  # Testo grigio #343C40
        pdf.cell(50, 7, 'Nome e Cognome:', ln=False)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, person_name, ln=True)

        if person_email:
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(50, 7, 'Email:', ln=False)
            pdf.cell(0, 7, person_email, ln=True)

        if person_extension:
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(50, 7, 'Interno:', ln=False)
            pdf.cell(0, 7, person_extension, ln=True)

        if person_mobile_phone:
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(50, 7, 'Cellulare:', ln=False)
            pdf.cell(0, 7, person_mobile_phone, ln=True)

        if person_department:
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(50, 7, 'Reparto:', ln=False)
            pdf.cell(0, 7, person_department, ln=True)

        if person_site:
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(50, 7, 'Sede:', ln=False)
            pdf.cell(0, 7, person_site, ln=True)

        pdf.ln(5)

        # CREDENZIALI (PRIMA del materiale assegnato)
        if password or pin_sim or pin_sblocco:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_fill_color(255, 221, 15)
            pdf.set_text_color(81, 93, 100)
            pdf.cell(0, 8, 'CREDENZIALI', fill=True, ln=True)

            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(52, 60, 64)

            if password:
                pdf.cell(50, 7, 'Password:', ln=False)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(0, 7, password, ln=True)
                pdf.set_font('Helvetica', '', 10)

            if pin_sim:
                pdf.cell(50, 7, 'PIN SIM:', ln=False)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(0, 7, pin_sim, ln=True)
                pdf.set_font('Helvetica', '', 10)

            if pin_sblocco:
                pdf.cell(50, 7, 'PIN Sblocco:', ln=False)
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(0, 7, pin_sblocco, ln=True)

            pdf.ln(5)

        # Tabella materiali assegnati
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(255, 221, 15)
        pdf.set_text_color(81, 93, 100)
        pdf.cell(0, 8, 'MATERIALE ASSEGNATO', fill=True, ln=True)

        # Header tabella
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_fill_color(81, 93, 100)  # brand gray
        pdf.set_text_color(255, 255, 255)
        pdf.cell(15, 7, '#', border=1, fill=True, align='C')
        pdf.cell(30, 7, 'Tipo', border=1, fill=True, align='C')
        pdf.cell(90, 7, 'Descrizione', border=1, fill=True, align='C')
        pdf.cell(20, 7, 'Qta', border=1, fill=True, align='C')
        pdf.cell(35, 7, 'S/N', border=1, fill=True, align='C')
        pdf.ln()

        # Righe tabella
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(52, 60, 64)
        for idx, item in enumerate(items, 1):
            pdf.cell(15, 7, str(idx), border=1, align='C')
            pdf.cell(30, 7, item.get('type', 'N/A'), border=1, align='C')
            pdf.cell(90, 7, item.get('description', 'N/A')[:45], border=1)
            pdf.cell(20, 7, str(item.get('quantity', 1)), border=1, align='C')
            pdf.cell(35, 7, item.get('serial', '-')[:15] if item.get('serial') else '-', border=1, align='C')
            pdf.ln()

        pdf.ln(5)

        # Note
        if notes:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_fill_color(255, 221, 15)
            pdf.set_text_color(81, 93, 100)
            pdf.cell(0, 8, 'NOTE', fill=True, ln=True)

            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(52, 60, 64)
            pdf.multi_cell(0, 6, notes)
            pdf.ln(5)
        
        # Sezione firme
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(255, 221, 15)
        pdf.set_text_color(81, 93, 100)
        pdf.cell(0, 8, 'FIRME', fill=True, ln=True)
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(52, 60, 64)
        
        # Due colonne per le firme
        col_width = 90
        pdf.cell(col_width, 7, 'Il Dipendente', align='C')
        pdf.cell(col_width, 7, 'Operatore IT', align='C')
        pdf.ln(20)
        
        pdf.cell(col_width, 7, '_' * 35, align='C')
        pdf.cell(col_width, 7, '_' * 35, align='C')
        pdf.ln(5)
        
        pdf.set_font('Helvetica', 'I', 8)
        pdf.cell(col_width, 5, f'({person_name})', align='C')
        pdf.cell(col_width, 5, '(Firma e timbro)', align='C')
        pdf.ln(10)
        
        filename = f"{assignment_number.replace('/', '-')}.pdf"
        output_path = cls.OUTPUT_DIR / filename
        pdf.output(str(output_path))

        # Ritorna percorso relativo
        return f"/data/documents/{filename}"

    @classmethod
    def generate_restitution_pdf(
        cls,
        asset_code: str,
        asset_manufacturer: str,
        asset_model: str,
        asset_serial: str,
        person_name: str,
        person_site: Optional[str],
        assignment_date: date,
        restitution_date: date,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        logo_path: Optional[str] = None,
        footer_path: Optional[str] = None,
    ) -> str:
        """
        Genera il PDF del modulo di restituzione

        Returns:
            str: Percorso relativo del file PDF generato
        """
        # Assicura che la directory esista
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Risolvi percorsi logo e footer
        full_logo_path = None
        full_footer_path = None
        if logo_path:
            full_logo_path = str(cls.BASE_PATH / logo_path.lstrip("/"))
        if footer_path:
            full_footer_path = str(cls.BASE_PATH / footer_path.lstrip("/"))

        # Crea PDF
        pdf = AssignmentPDF(logo_path=full_logo_path, footer_path=full_footer_path)
        pdf.add_page()

        # Titolo
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(81, 93, 100)  # brand gray #515D64
        pdf.cell(0, 10, 'MODULO DI RESTITUZIONE MATERIALE', align='C', ln=True)
        pdf.ln(5)

        # Data restituzione
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, f'Data Restituzione: {restitution_date.strftime("%d/%m/%Y")}', ln=True)
        pdf.ln(5)

        # Dati dipendente
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(255, 221, 15)  # brand yellow #FFDD0F
        pdf.set_text_color(81, 93, 100)
        pdf.cell(0, 8, 'DATI DIPENDENTE', fill=True, ln=True)

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(52, 60, 64)  # Testo grigio #343C40
        pdf.cell(50, 7, 'Nome e Cognome:', ln=False)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, person_name, ln=True)

        if person_site:
            pdf.set_font('Helvetica', '', 10)
            pdf.cell(50, 7, 'Sede:', ln=False)
            pdf.cell(0, 7, person_site, ln=True)

        pdf.ln(5)

        # Dati asset
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(255, 221, 15)
        pdf.set_text_color(81, 93, 100)
        pdf.cell(0, 8, 'MATERIALE RESTITUITO', fill=True, ln=True)

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(52, 60, 64)
        
        pdf.cell(50, 7, 'Codice Asset:', ln=False)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, asset_code if asset_code else 'N/A', ln=True)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(50, 7, 'Marca:', ln=False)
        pdf.cell(0, 7, asset_manufacturer, ln=True)
        
        pdf.cell(50, 7, 'Modello:', ln=False)
        pdf.cell(0, 7, asset_model, ln=True)
        
        pdf.cell(50, 7, 'Numero Seriale:', ln=False)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, asset_serial, ln=True)

        pdf.ln(5)

        # Periodo di utilizzo
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(255, 221, 15)
        pdf.set_text_color(81, 93, 100)
        pdf.cell(0, 8, 'PERIODO DI UTILIZZO', fill=True, ln=True)

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(52, 60, 64)
        
        pdf.cell(50, 7, 'Data Assegnazione:', ln=False)
        pdf.cell(0, 7, assignment_date.strftime("%d/%m/%Y"), ln=True)
        
        pdf.cell(50, 7, 'Data Restituzione:', ln=False)
        pdf.cell(0, 7, restitution_date.strftime("%d/%m/%Y"), ln=True)
        
        # Calcola giorni di utilizzo
        giorni_utilizzo = (restitution_date - assignment_date).days
        pdf.cell(50, 7, 'Giorni di Utilizzo:', ln=False)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, str(giorni_utilizzo), ln=True)

        pdf.ln(5)

        # Motivo restituzione
        if reason:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_fill_color(255, 221, 15)
            pdf.set_text_color(81, 93, 100)
            pdf.cell(0, 8, 'MOTIVO RESTITUZIONE', fill=True, ln=True)

            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(52, 60, 64)
            pdf.multi_cell(0, 6, reason)
            pdf.ln(5)

        # Note
        if notes:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_fill_color(255, 221, 15)
            pdf.set_text_color(81, 93, 100)
            pdf.cell(0, 8, 'NOTE', fill=True, ln=True)

            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(52, 60, 64)
            pdf.multi_cell(0, 6, notes)
            pdf.ln(5)

        # Sezione firme
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(255, 221, 15)
        pdf.set_text_color(81, 93, 100)
        pdf.cell(0, 8, 'FIRME', fill=True, ln=True)
        pdf.ln(5)

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(52, 60, 64)

        # Due colonne per le firme
        col_width = 90
        pdf.cell(col_width, 7, 'Il Dipendente', align='C')
        pdf.cell(col_width, 7, 'Operatore IT', align='C')
        pdf.ln(20)

        pdf.cell(col_width, 7, '_' * 35, align='C')
        pdf.cell(col_width, 7, '_' * 35, align='C')
        pdf.ln(5)

        pdf.set_font('Helvetica', 'I', 8)
        pdf.cell(col_width, 5, f'({person_name})', align='C')
        pdf.cell(col_width, 5, '(Firma e timbro)', align='C')
        pdf.ln(10)

        # Genera nome file
        filename = f"REST_{asset_code.replace('/', '-') if asset_code else asset_serial}_{restitution_date.strftime('%Y%m%d')}.pdf"
        output_path = cls.OUTPUT_DIR / filename
        pdf.output(str(output_path))

        # Ritorna percorso relativo
        return f"/data/documents/{filename}"

    @classmethod
    def generate_substitution_pdf(
        cls,
        assignment_number: str,
        assignment_date: date,
        person_name: str,
        person_email: str,
        person_extension: Optional[str],
        person_mobile_phone: Optional[str],
        person_site: Optional[str],
        returned_items: List[Dict],  # Materiali ritirati
        assigned_items: List[Dict],  # Materiali nuovi assegnati
        notes: Optional[str] = None,
        logo_path: Optional[str] = None,
        footer_path: Optional[str] = None,
        pin_sim: Optional[str] = None,  # PIN SIM decriptato (se presenti SIM negli assigned_items)
    ) -> str:
        """
        Genera il PDF del modulo di sostituzione materiale.
        Include sia la sezione di ritiro che quella di assegnazione.
        NON include credenziali (già fornite in precedenza).
        
        Args:
            assignment_number: Numero assegnazione (es: ASS-2026-024)
            assignment_date: Data operazione
            person_name: Nome completo dipendente
            person_email: Email dipendente
            person_extension: Interno telefonico
            person_mobile_phone: Numero cellulare
            person_site: Sede
            returned_items: Lista materiali restituiti [{'type': 'Asset', 'description': '...', 'serial': '...', 'quantity': 1}]
            assigned_items: Lista materiali assegnati [{'type': 'Asset', 'description': '...', 'serial': '...', 'quantity': 1}]
            notes: Note aggiuntive
            logo_path: Path logo aziendale
            footer_path: Path footer aziendale
            
        Returns:
            str: Percorso relativo del file PDF generato
        """
        # Assicura che la directory esista
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # Risolvi percorsi logo e footer
        full_logo_path = None
        full_footer_path = None
        if logo_path:
            full_logo_path = str(cls.BASE_PATH / logo_path.lstrip("/"))
        if footer_path:
            full_footer_path = str(cls.BASE_PATH / footer_path.lstrip("/"))

        # Crea PDF
        pdf = AssignmentPDF(logo_path=full_logo_path, footer_path=full_footer_path)
        pdf.add_page()

        # TITOLO PRINCIPALE
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(81, 93, 100)
        pdf.cell(0, 10, 'MODULO DI SOSTITUZIONE MATERIALE', align='C', ln=True)
        pdf.ln(2)

        # Numero e data
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f'N° {assignment_number}  |  Data: {assignment_date.strftime("%d/%m/%Y")}', align='C', ln=True)
        pdf.ln(5)

        # ============================================
        # SEZIONE 1: DATI DIPENDENTE
        # ============================================
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(255, 221, 15)
        pdf.set_text_color(81, 93, 100)
        pdf.cell(0, 8, 'DATI DIPENDENTE', fill=True, ln=True)

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(52, 60, 64)
        
        pdf.cell(50, 7, 'Nome e Cognome:', ln=False)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 7, person_name, ln=True)

        pdf.set_font('Helvetica', '', 10)
        pdf.cell(50, 7, 'Email:', ln=False)
        pdf.cell(0, 7, person_email, ln=True)

        if person_extension:
            pdf.cell(50, 7, 'Interno:', ln=False)
            pdf.cell(0, 7, person_extension, ln=True)

        if person_mobile_phone:
            pdf.cell(50, 7, 'Numero Cellulare:', ln=False)
            pdf.cell(0, 7, person_mobile_phone, ln=True)

        if person_site:
            pdf.cell(50, 7, 'Sede:', ln=False)
            pdf.cell(0, 7, person_site, ln=True)

        pdf.ln(5)

        # ============================================
        # SEZIONE 2: MATERIALE RESTITUITO
        # ============================================
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(255, 99, 71)  # Rosso/Arancione per ritiro
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, 'MATERIALE RESTITUITO', fill=True, ln=True)

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(52, 60, 64)

        # Tabella header
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(15, 7, 'Tipo', border=1, fill=True)
        pdf.cell(90, 7, 'Descrizione', border=1, fill=True)
        pdf.cell(60, 7, 'Numero Seriale', border=1, fill=True)
        pdf.cell(15, 7, 'Qta', border=1, fill=True, align='C')
        pdf.ln()

        # Righe materiale restituito
        for item in returned_items:
            pdf.cell(15, 7, item.get('type', 'N/A')[:4], border=1)
            pdf.cell(90, 7, item.get('description', 'N/A')[:50], border=1)
            pdf.cell(60, 7, (item.get('serial') or 'N/A')[:30], border=1)
            pdf.cell(15, 7, str(item.get('quantity', 1)), border=1, align='C')
            pdf.ln()

        pdf.ln(5)

        # ============================================
        # SEZIONE 3: MATERIALE ASSEGNATO
        # ============================================
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(34, 197, 94)  # Verde per nuova assegnazione
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 8, 'MATERIALE ASSEGNATO', fill=True, ln=True)

        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(52, 60, 64)

        # Tabella header
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(15, 7, 'Tipo', border=1, fill=True)
        pdf.cell(90, 7, 'Descrizione', border=1, fill=True)
        pdf.cell(60, 7, 'Numero Seriale', border=1, fill=True)
        pdf.cell(15, 7, 'Qta', border=1, fill=True, align='C')
        pdf.ln()

        # Righe materiale assegnato
        for item in assigned_items:
            pdf.cell(15, 7, item.get('type', 'N/A')[:4], border=1)
            pdf.cell(90, 7, item.get('description', 'N/A')[:50], border=1)
            pdf.cell(60, 7, (item.get('serial') or 'N/A')[:30], border=1)
            pdf.cell(15, 7, str(item.get('quantity', 1)), border=1, align='C')
            pdf.ln()

        pdf.ln(5)

        # ============================================
        # SEZIONE 4: NOTE (se presenti)
        # ============================================
        if notes:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_fill_color(255, 221, 15)
            pdf.set_text_color(81, 93, 100)
            pdf.cell(0, 8, 'NOTE', fill=True, ln=True)

            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(52, 60, 64)
            pdf.multi_cell(0, 6, notes)
            pdf.ln(5)

        # ============================================
        # SEZIONE 5: FIRME
        # ============================================
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_fill_color(255, 221, 15)
        pdf.set_text_color(81, 93, 100)
        pdf.cell(0, 8, 'FIRME', fill=True, ln=True)
        pdf.ln(5)

        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(52, 60, 64)

        # Due colonne per le firme
        col_width = 90
        pdf.cell(col_width, 7, 'Il Dipendente', align='C')
        pdf.cell(col_width, 7, 'Operatore IT', align='C')
        pdf.ln(20)

        pdf.cell(col_width, 7, '_' * 35, align='C')
        pdf.cell(col_width, 7, '_' * 35, align='C')
        pdf.ln(5)

        pdf.set_font('Helvetica', 'I', 8)
        pdf.cell(col_width, 5, f'({person_name})', align='C')
        pdf.cell(col_width, 5, '(Amministratore IT)', align='C')

        # Salva PDF
        filename = f"{assignment_number.replace('/', '-')}.pdf"
        pdf_path = cls.OUTPUT_DIR / filename
        pdf.output(str(pdf_path))

        return f"/data/documents/{filename}"

    @classmethod
    def generate_return_pdf(
        cls,
        assignment_number: str,
        assignment_date: date,
        person_name: str,
        person_email: str,
        person_extension: Optional[str],
        person_mobile_phone: Optional[str],
        person_site: Optional[str],
        returned_items: List[Dict],  # Materiali ritirati
        notes: Optional[str] = None,
        logo_path: Optional[str] = None,
        footer_path: Optional[str] = None,
    ) -> str:
        """
        Genera il PDF del modulo di riconsegna materiale.
        Include SOLO la sezione materiali restituiti (NO assegnazione, NO credenziali).

        Args:
            assignment_number: Numero assegnazione (es: ASS-2026-030)
            assignment_date: Data riconsegna
            person_name: Nome completo dipendente
            person_email: Email dipendente
            person_extension: Interno telefonico
            person_mobile_phone: Numero cellulare
            person_site: Sede
            returned_items: Lista materiali restituiti [{'type': 'Asset', 'description': '...', 'serial': '...', 'quantity': 1}]
            notes: Note aggiuntive
            logo_path: Path logo aziendale
            footer_path: Path footer aziendale

        Returns:
            str: Percorso relativo del file PDF generato
        """
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        full_logo_path = str(cls.BASE_PATH / logo_path.lstrip("/")) if logo_path else None
        full_footer_path = str(cls.BASE_PATH / footer_path.lstrip("/")) if footer_path else None

        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=False)

        # LOGO (se presente)
        if full_logo_path:
            logo_full_path = Path(full_logo_path)
            if logo_full_path.exists():
                try:
                    pdf.image(str(logo_full_path), x=10, y=10, w=190)
                    pdf.ln(35)
                except Exception as e:
                    logger.error("Errore caricamento logo: %s", e)
                    pdf.ln(10)
            else:
                pdf.ln(10)
        else:
            pdf.ln(10)

        # TITOLO
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, 'RICONSEGNA MATERIALE AZIENDALE', ln=True, align='C')
        pdf.ln(5)

        # INFO ASSEGNAZIONE
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(0, 6, f"Numero: {assignment_number}", ln=True)
        pdf.cell(0, 6, f"Data: {assignment_date.strftime('%d/%m/%Y')}", ln=True)
        pdf.ln(3)

        # DATI DIPENDENTE
        pdf.set_font('Helvetica', 'B', 11)
        pdf.cell(0, 8, 'DATI DIPENDENTE', ln=True)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f"Nome: {person_name}", ln=True)
        pdf.cell(0, 6, f"Email: {person_email}", ln=True)
        if person_extension:
            pdf.cell(0, 6, f"Interno: {person_extension}", ln=True)
        if person_mobile_phone:
            pdf.cell(0, 6, f"Cellulare: {person_mobile_phone}", ln=True)
        if person_site:
            pdf.cell(0, 6, f"Sede: {person_site}", ln=True)
        pdf.ln(5)

        # SEZIONE MATERIALE RESTITUITO
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_fill_color(255, 200, 200)  # Rosso chiaro
        pdf.cell(0, 8, 'MATERIALE RESTITUITO', ln=True, fill=True)
        pdf.ln(2)

        # Tabella materiali restituiti
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(30, 7, 'Tipo', border=1, align='C')
        pdf.cell(90, 7, 'Descrizione', border=1, align='C')
        pdf.cell(50, 7, 'Seriale', border=1, align='C')
        pdf.cell(20, 7, 'Qta', border=1, align='C')
        pdf.ln()

        pdf.set_font('Helvetica', '', 8)
        for item in returned_items:
            pdf.cell(30, 6, item.get('type', 'N/A')[:20], border=1)
            pdf.cell(90, 6, item.get('description', 'N/A')[:50], border=1)
            pdf.cell(50, 6, (item.get('serial') or 'N/A')[:30], border=1)
            pdf.cell(20, 6, str(item.get('quantity', 1)), border=1, align='C')
            pdf.ln()

        pdf.ln(5)

        # NOTE (se presenti)
        if notes:
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 6, 'Note:', ln=True)
            pdf.set_font('Helvetica', '', 9)
            pdf.multi_cell(0, 5, notes)
            pdf.ln(3)

        # FIRME
        pdf.ln(10)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(95, 6, 'Il Dipendente', align='C')
        pdf.cell(95, 6, 'Operatore IT', align='C')
        pdf.ln(15)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(95, 6, '_' * 40, align='C')
        pdf.cell(95, 6, '_' * 40, align='C')

        # FOOTER (se presente)
        if full_footer_path:
            footer_full_path = Path(full_footer_path)
            if footer_full_path.exists():
                try:
                    pdf.set_y(270)
                    pdf.image(str(footer_full_path), x=10, y=270, w=190)
                except Exception as e:
                    logger.error("Errore caricamento footer: %s", e)

        # Salva PDF
        filename = f"{assignment_number.replace('/', '-')}.pdf"
        output_path = cls.OUTPUT_DIR / filename
        pdf.output(str(output_path))

        return f"/data/documents/{filename}"
