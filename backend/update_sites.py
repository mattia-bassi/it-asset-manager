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

def api_put(path, body):
    req = urllib.request.Request(f'https://localhost:8000{path}', json.dumps(body).encode(), method='PUT')
    req.add_header('Authorization', 'Bearer ' + token)
    req.add_header('Content-Type', 'application/json')
    return json.loads(urllib.request.urlopen(req, context=ctx).read())

def api_post(path, body):
    req = urllib.request.Request(f'https://localhost:8000{path}', json.dumps(body).encode(), method='POST')
    req.add_header('Authorization', 'Bearer ' + token)
    req.add_header('Content-Type', 'application/json')
    return json.loads(urllib.request.urlopen(req, context=ctx).read())

# Get current sites
sites_data = api_get('/api/sites?limit=100')
site_by_name = {}
for s in sites_data['items']:
    site_by_name[s['name'].lower()] = s['id']

print("Sedi attuali:", site_by_name)

# Updates for existing sites
updates = {
    'roma': {'address': 'Viale Erminio Spalla, 9', 'city': 'Roma', 'zip_code': '00142', 'country': 'Italia', 'phone': '+39 06 45761'},
    'milano': {'address': 'Viale Vittorio Veneto, 2', 'city': 'Milano', 'zip_code': '20124', 'country': 'Italia', 'phone': '+39 02 97673350'},
    'napoli': {'address': 'Piazza Giovanni Bovio, 22', 'city': 'Napoli', 'zip_code': '80133', 'country': 'Italia', 'phone': '+39 081 4206442'},
    'perugia': {'address': 'Via Mario Angeloni, 80/B', 'city': 'Perugia', 'zip_code': '06124', 'country': 'Italia', 'phone': '+39 075 5280483'},
    'potenza': {'address': 'Via del Popolo, 62', 'city': 'Potenza', 'zip_code': '85100', 'country': 'Italia', 'phone': '+39 0971 36250'},
    'cagliari': {'address': 'Viale Regina Margherita, 6', 'city': 'Cagliari', 'zip_code': '09125', 'country': 'Italia', 'phone': '+39 070 653463'},
    'palermo': {'address': 'Via Duca della Verdura, 4', 'city': 'Palermo', 'zip_code': '90143', 'country': 'Italia', 'phone': '+39 091 7783200'},
}

# Update existing
for name, data in updates.items():
    if name in site_by_name:
        sid = site_by_name[name]
        try:
            r = api_put(f'/api/sites/{sid}', data)
            print(f"[UPD] {name.title()} (id={sid}) -> aggiornata")
        except urllib.error.HTTPError as e:
            print(f"[!!] {name.title()}: {e.code} {e.read().decode()}")

# Create new sites (Venafro + Rieti)
new_sites = [
    {'name': 'Venafro', 'address': 'Corso Pietro Lucenteforte, 5', 'city': 'Venafro (IS)', 'zip_code': '86079', 'country': 'Italia', 'phone': '+39 0865 909822'},
    {'name': 'Rieti', 'address': 'Via Dupre Theseider, 119', 'city': 'Rieti', 'zip_code': '02100', 'country': 'Italia', 'phone': '+39 0746 202007'},
]

for s in new_sites:
    if s['name'].lower() in site_by_name:
        print(f"[SKIP] {s['name']} (gia presente)")
        continue
    try:
        r = api_post('/api/sites', s)
        print(f"[NEW] {s['name']} -> id={r['id']}")
    except urllib.error.HTTPError as e:
        print(f"[!!] {s['name']}: {e.code} {e.read().decode()}")

print("\nDone!")
