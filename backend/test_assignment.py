import json, urllib.request, urllib.parse, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

data = urllib.parse.urlencode({'username':'admin','password':'Admin_2025!!'}).encode()
req = urllib.request.Request('https://localhost:8000/api/auth/login', data=data, method='POST')
req.add_header('Content-Type','application/x-www-form-urlencoded')
token = json.loads(urllib.request.urlopen(req, context=ctx).read())['access_token']

def api_get(path):
    req = urllib.request.Request(f'https://localhost:8000{path}')
    req.add_header('Authorization', 'Bearer ' + token)
    return json.loads(urllib.request.urlopen(req, context=ctx).read())

def api_post(path, body):
    req = urllib.request.Request(f'https://localhost:8000{path}', json.dumps(body).encode(), method='POST')
    req.add_header('Authorization', 'Bearer ' + token)
    req.add_header('Content-Type', 'application/json')
    resp = urllib.request.urlopen(req, context=ctx)
    return json.loads(resp.read())

# 1. Find Abbati Mara
people = api_get('/api/people?search=Abbati&limit=10')
mara = None
for p in people['items']:
    if p['first_name'].lower() == 'mara' and p['last_name'].lower() == 'abbati':
        mara = p
        break

if not mara:
    print("[!!] Abbati Mara non trovata!")
    exit(1)

print(f"[OK] Persona: {mara['last_name']} {mara['first_name']} -> id={mara['id']}")

# 2. Find asset PF2SR8XD
assets = api_get('/api/assets?search=PF2SR8XD&limit=10')
laptop = None
for a in assets['items']:
    if a['serial_number'] == 'PF2SR8XD':
        laptop = a
        break

if not laptop:
    print("[!!] Asset PF2SR8XD non trovato!")
    exit(1)

print(f"[OK] Asset: {laptop['model']} sn={laptop['serial_number']} -> id={laptop['id']} status={laptop['status']}")

# 3. Create assignment
assignment = {
    "person_id": mara['id'],
    "assignment_date": "2026-02-25",
    "assignment_type": "assegnazione",
    "status": "attivo",
    "notes": "Import da CSV dotazione materiale informatico",
    "items": [
        {
            "item_type": "asset",
            "asset_id": laptop['id'],
            "quantity": 1
        }
    ]
}

try:
    r = api_post('/api/assignments', assignment)
    print(f"[OK] Assegnazione creata: id={r['id']} numero={r.get('assignment_number','N/A')}")
    print(f"     {mara['last_name']} {mara['first_name']} <- {laptop['model']} ({laptop['serial_number']})")
except urllib.error.HTTPError as e:
    print(f"[!!] Errore: {e.code} {e.read().decode()}")
