import csv, json, urllib.request, urllib.parse, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Login
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

# 1. Load sites map
sites_data = api_get('/api/sites?limit=100')
site_map = {}
for s in sites_data['items']:
    site_map[s['name'].lower()] = s['id']

# 2. Load existing people
people_data = api_get('/api/people?limit=1000')
people_map = {}
for p in people_data['items']:
    key = (p['last_name'].lower().strip(), p['first_name'].lower().strip())
    people_map[key] = p['id']

# 3. Load existing assets by serial
assets_data = api_get('/api/assets?limit=1000')
existing_serials = {}
for a in assets_data['items']:
    existing_serials[a['serial_number'].upper().strip()] = a['id']

# 4. Model normalization
def normalize_model(raw):
    raw = raw.strip().upper()
    raw = raw.replace('LENOVOT14S', 'LENOVO T14S').replace('LENOVOT14', 'LENOVO T14')
    raw = raw.replace('LENOVO ', '')
    mapping = {
        'T14': 'ThinkPad T14',
        'T14S': 'ThinkPad T14s',
        'T14 GEN1': 'ThinkPad T14 Gen 1',
        'T14 GEN2': 'ThinkPad T14 Gen 2',
        'T14S GEN1': 'ThinkPad T14s Gen 1',
        'T14S GEN2': 'ThinkPad T14s Gen 2',
        'T490': 'ThinkPad T490',
        'T490S': 'ThinkPad T490s',
        'THINKBOOK 15-IML': 'ThinkBook 15-IML',
        'THINKBOOK 14 G2 ITL': 'ThinkBook 14 G2 ITL',
    }
    return mapping.get(raw.strip(), raw.strip())

# 5. Person name parsing (same logic as import)
def parse_name(nominativo):
    nominativo = ' '.join(nominativo.replace('\xa0', ' ').split()).strip()
    non_persons = ['SALA CONSIGLIO', 'SALA RIUNIONI', 'DIREZIONE MILANO']
    if nominativo in non_persons:
        return None, None
    
    inverted = {
        'STEFANO MEZZERA': ('MEZZERA', 'STEFANO'),
        'LUCIA CORVO': ('CORVO', 'LUCIA'),
        'MARCO MIGNOSI': ('MIGNOSI', 'MARCO'),
        'FRANCESCA LIRONI': ('LIRONI', 'FRANCESCA'),
    }
    if nominativo in inverted:
        return inverted[nominativo]
    
    compounds = [
        'AVOLIO DE MARTINO', 'COTTA RAMUSINO', 'DELLA MARTORA',
        'DEL FORNO', 'LA SCALEIA'
    ]
    for c in compounds:
        if nominativo.startswith(c + ' '):
            return c.title(), nominativo[len(c)+1:].title()
    
    prefixes = ["D'", "DE ", "DI "]
    for pfx in prefixes:
        if nominativo.startswith(pfx):
            rest = nominativo[len(pfx):]
            parts = rest.split(' ', 1)
            cognome = pfx + parts[0]
            nome = parts[1] if len(parts) > 1 else ''
            return cognome.title(), nome.title()
    
    parts = nominativo.split(' ', 1)
    cognome = parts[0].title()
    nome = parts[1].title() if len(parts) > 1 else ''
    return cognome, nome

# 6. Read CSV and process
csv_path = '/tmp/dotazione.csv'
# Copy CSV first

stats = {'assets_created': 0, 'assets_skipped': 0, 'assignments_created': 0, 
         'assignments_skipped': 0, 'errors': 0, 'non_persons': 0}

with open(csv_path, 'r', encoding='latin-1') as f:
    reader = csv.reader(f, delimiter=';')
    header = next(reader)
    
    for row in reader:
        nominativo = row[0].strip().replace('\xa0', ' ').strip()
        if not nominativo:
            continue
        
        sede = row[1].strip().replace('\xa0', '').strip().title()
        model_raw = row[2].strip().replace('\xa0', ' ').strip()
        serial = row[3].strip().replace('\xa0', '').strip().upper()
        
        if not serial:
            continue
        
        # Parse person
        cognome, nome = parse_name(nominativo.upper())
        if cognome is None:
            stats['non_persons'] += 1
            continue
        
        # Find person
        person_key = (cognome.lower().strip(), nome.lower().strip())
        person_id = people_map.get(person_key)
        if not person_id:
            print(f"[WARN] Persona non trovata: {cognome} {nome}")
            stats['errors'] += 1
            continue
        
        # Find site
        site_id = site_map.get(sede.lower(), 1)  # default Roma
        
        # Normalize model
        model = normalize_model(model_raw)
        
        # Create or find asset
        asset_id = existing_serials.get(serial)
        if asset_id:
            stats['assets_skipped'] += 1
        else:
            asset_body = {
                "asset_code": serial,
                "serial_number": serial,
                "manufacturer": "Lenovo",
                "model": model,
                "asset_type_id": 4,
                "site_id": site_id,
                "status": "disponibile",
                "is_active": True
            }
            try:
                r = api_post('/api/assets', asset_body)
                asset_id = r['id']
                existing_serials[serial] = asset_id
                stats['assets_created'] += 1
            except urllib.error.HTTPError as e:
                err = e.read().decode()
                print(f"[!!] Asset {serial}: {e.code} {err}")
                stats['errors'] += 1
                continue
        
        # Check if already assigned (asset status)
        try:
            asset_info = api_get(f'/api/assets/{asset_id}')
            if asset_info['status'] == 'assegnato':
                stats['assignments_skipped'] += 1
                continue
        except:
            pass
        
        # Create assignment
        assignment_body = {
            "person_id": person_id,
            "assignment_date": "2026-02-25",
            "assignment_type": "assegnazione",
            "status": "attivo",
            "notes": "Import massivo da CSV dotazione materiale",
            "items": [{"item_type": "asset", "asset_id": asset_id, "quantity": 1}]
        }
        try:
            r = api_post('/api/assignments', assignment_body)
            print(f"[OK] {cognome} {nome} <- {model} ({serial}) ASS={r.get('assignment_number','')}")
            stats['assignments_created'] += 1
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            print(f"[!!] Assign {cognome} {nome} <- {serial}: {e.code} {err}")
            stats['errors'] += 1

print(f"\n{'='*60}")
print(f"Asset creati:         {stats['assets_created']}")
print(f"Asset gia esistenti:  {stats['assets_skipped']}")
print(f"Assegnazioni create:  {stats['assignments_created']}")
print(f"Assegnazioni skip:    {stats['assignments_skipped']}")
print(f"Non-persone:          {stats['non_persons']}")
print(f"Errori:               {stats['errors']}")
