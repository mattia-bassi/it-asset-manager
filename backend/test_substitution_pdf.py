import sys
sys.path.insert(0, '/app')
from app.db.session import SessionLocal
from app.services.assignment_service import AssignmentService
from app.services.person_service import PersonService
from app.services.document_template_service import DocumentTemplateService
from app.services.pdf_generator_service import PDFGeneratorService

db = SessionLocal()

try:
    # Recupera assignment
    assignment = AssignmentService.get_by_id(db, 28)
    person = PersonService.get_by_id(db, assignment.person_id)
    
    # Prepara items assegnati
    assigned_items = []
    for item in assignment.items:
        if not item.is_returned:
            item_dict = {
                'type': 'Asset' if item.item_type == 'asset' else 'Materiale',
                'description': item.item_description,
                'quantity': item.quantity,
                'serial': None
            }
            assigned_items.append(item_dict)
    
    # Prepara items restituiti
    returned_items = []
    for item in assignment.items:
        if item.is_returned:
            ret_item_dict = {
                'type': 'Asset' if item.item_type == 'asset' else 'Materiale',
                'description': item.item_description,
                'quantity': item.quantity,
                'serial': None
            }
            returned_items.append(ret_item_dict)
    
    print('Assigned items:', len(assigned_items))
    print('Returned items:', len(returned_items))
    print('Assignment number:', assignment.assignment_number)
    print('Person name:', f'{person.first_name} {person.last_name}')
    
    # Genera PDF
    pdf_path = PDFGeneratorService.generate_substitution_pdf(
        assignment_number=assignment.assignment_number,
        assignment_date=assignment.assignment_date,
        person_name=f'{person.first_name} {person.last_name}',
        person_email=person.email,
        person_extension=person.extension,
        person_mobile_phone=person.mobile_phone,
        person_site=None,
        returned_items=returned_items,
        assigned_items=assigned_items,
        notes=assignment.notes
    )
    print('SUCCESS! PDF generated:', pdf_path)
    
except Exception as e:
    print('ERROR:', type(e).__name__, str(e))
    import traceback
    traceback.print_exc()
finally:
    db.close()
