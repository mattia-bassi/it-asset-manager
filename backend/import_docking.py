import csv, json, urllib.request, urllib.parse, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

data = urllib.parse.urlencode({'username':'admin','password':'Admin_2025!!'}).encode()
req = urllib.request.Request('https://localhost:8000/api/auth/login', data=data, method='POST')
req.add_header('Content-Type','application/x-www-form-urlencoded')
token = json.loads(urllib.request.urlopen(req, context=ctx).read())['access_token']

def api_get(path):
    r = urllib.request.Request(f'https://localhost:8000{path}')
    r.add_header('Authorization', 'Bearer ' + token)
    return json.loads(urllib.request.urlopen(r, context=ctx).read())

def api_post(path, body):
    r = urllib.request.Request(f'https://localhost:8000{path}', json.dumps(body).encode(), method='POST')
    r.add_header('Authorization', 'Bearer ' + token)
    r.add_header('Content-Type', 'application/json')
    return json.loads(urllib.request.urlopen(r, context=ctx).read())

# Load maps
sites_data = api_get('/api/sites?limit=100')
site_map = {s['name'].lower(): s['id'] for s in sites_data['items']}

people_data = api_get('/api/people?limit=1000')
people_map = {}
for p in people_data['items']:
    key = (p['last_name'].lower().strip(), p['first_name'].lower().strip())
    people_map[key] = p['id']

assets_data = api_get('/api/assets?limit=1000')
existing_serials = {a['serial_number'].upper().strip(): a['id'] for a in assets_data['items']}

def parse_name(nom):
    nom = ' '.join(nom.replace('\xa0', ' ').split()).strip()
    non_persons = ['SALA CONSIGLIO', 'SALA RIUNIONI', 'DIREZIONE MILANO']
    if nom in non_persons:
        return None, None
    inverted = {
        'STEFANO MEZZERA': ('MEZZERA', 'STEFANO'),
        'LUCIA CORVO': ('CORVO', 'LUCIA'),
        'MARCO MIGNOSI': ('MIGNOSI', 'MARCO'),
        'FRANCESCA LIRONI': ('LIRONI', 'FRANCESCA'),
    }
    if nom in inverted:
        return inverted[nom]
    compounds = ['AVOLIO DE MARTINO', 'COTTA RAMUSINO', 'DELLA MARTORA', 'DEL FORNO', 'LA SCALEIA']
    for c in compounds:
        if nom.startswith(c + ' '):
            return c.title(), nom[len(c)+1:].title()
    for pfx in ["D'", "DE ", "DI "]:
        if nom.startswith(pfx):
            rest = nom[len(pfx):]
            parts = rest.split(' ', 1)
            return (pfx + parts[0]).title(), parts[1].title() if len(parts) > 1 else ''
    parts = nom.split(' ', 1)
    return parts[0].title(), parts[1].title() if len(parts) > 1 else ''

stats = {'created': 0, 'skipped_exists': 0, 'skipped_no_serial': 0,
         'skipped_no_dock': 0, 'assigned': 0, 'assign_skip': 0, 'errors': 0, 'non_persons': 0}

with open('/tmp/dotazione.csv', 'r', encoding='latin-1') as f:
    reader = csv.reader(f, delimiter=';')
    header = next(reader)
    
    for row in reader:
        nominativo = row[0].strip().replace('\xa0', ' ').strip()
        if not nominativo:
            continue
        
        sede = row[1].strip().replace('\xa0', '').strip().title()
        has_dock = row[4].strip().replace('\xa0', '').strip().upper() if len(row) > 4 else ''
        dock_sn = row[5].strip().replace('\xa0', '').strip().upper() if len(row) > 5 else ''
        
        if has_dock != 'SI':
            stats['skipped_no_dock'] += 1
            continue
        
        # Clean serial
        dock_sn = dock_sn.replace(' ', '')
        
        # Skip "senza seriale" and empty
        if not dock_sn or 'SENZA' in dock_sn:
            stats['skipped_no_serial'] += 1
            continue
        
        cognome, nome = parse_name(nominativo.upper())
        if cognome is None:
            stats['non_persons'] += 1
            continue
        
        person_key = (cognome.lower().strip(), nome.lower().strip())
        person_id = people_map.get(person_key)
        if not person_id:
            print(f"[WARN] Persona non trovata: {cognome} {nome}")
            stats['errors'] += 1
            continue
        
        site_id = site_map.get(sede.lower(), 1)
        
        # Create or find asset
        asset_id = existing_serials.get(dock_sn)
        if asset_id:
            stats['skipped_exists'] += 1
        else:
            asset_body = {
                "asset_code": dock_sn,
                "serial_number": dock_sn,
                "manufacturer": "Lenovo",
                "model": "40AS",
                "asset_type_id": 15,
                "site_id": site_id,
                "status": "disponibile",
                "is_active": True
            }
            try:
                r = api_post('/api/assets', asset_body)
                asset_id = r['id']
                existing_serials[dock_sn] = asset_id
                stats['created'] += 1
            except urllib.error.HTTPError as e:
                err = e.read().decode()
                print(f"[!!] Dock {dock_sn}: {e.code} {err}")
                stats['errors'] += 1
                continue
        
        # Check if already assigned
        try:
            asset_info = api_get(f'/api/assets/{asset_id}')
            if asset_info['status'] == 'assegnato':
                stats['assign_skip'] += 1
                continue
        except:
            pass
        
        # Create assignment
        assignment_body = {
            "person_id": person_id,
            "assignment_date": "2026-02-25",
            "assignment_type": "assegnazione",
            "status": "attivo",
            "notes": "Import docking station da CSV dotazione",
            "items": [{"item_type": "asset", "asset_id": asset_id, "quantity": 1}]
        }
        try:
            r = api_post('/api/assignments', assignment_body)
            print(f"[OK] {cognome} {nome} <- Dock ({dock_sn}) ASS={r.get('assignment_number','')}")
            stats['assigned'] += 1
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            print(f"[!!] Assign {cognome} {nome} <- {dock_sn}: {e.code} {err}")
            stats['errors'] += 1

print(f"\n{'='*60}")
print(f"Docking create:       {stats['created']}")
print(f"Gia esistenti:        {stats['skipped_exists']}")
print(f"Assegnazioni create:  {stats['assigned']}")
print(f"Assegnazioni skip:    {stats['assign_skip']}")
print(f"No docking (NO):      {stats['skipped_no_dock']}")
print(f"Senza seriale:        {stats['skipped_no_serial']}")
print(f"Non-persone:          {stats['non_persons']}")
print(f"Errori:               {stats['errors']}")
