import json, urllib.request, urllib.parse, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Login
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
    return json.loads(urllib.request.urlopen(req, context=ctx).read())

# 1. Get sites map
sites_data = api_get('/api/sites?limit=100')
site_map = {}
for s in sites_data['items']:
    site_map[s['name'].lower()] = s['id']
print(f"Sedi trovate: {site_map}")

# 2. Get existing people
existing = api_get('/api/people?limit=1000')
existing_set = set()
for p in existing['items']:
    key = (p['last_name'].lower().strip(), p['first_name'].lower().strip())
    existing_set.add(key)
print(f"Persone esistenti: {len(existing_set)}")

# 3. People to import
people = [
    ("Abbati", "Mara", "Roma"),
    ("Abbati", "Marisa", "Roma"),
    ("Alano", "Antonio", "Napoli"),
    ("Albini", "Vincenzo", "Roma"),
    ("Alborello", "Serena", "Roma"),
    ("Allocca", "Adriana", "Roma"),
    ("Altezza", "Imma", "Napoli"),
    ("Amadori", "Alessandro", "Roma"),
    ("Ambrosetti", "Maria Elena", "Roma"),
    ("Avolio De Martino", "Oriana", "Napoli"),
    ("Barlozzini", "Sonia", "Roma"),
    ("Bassi", "Carlo", "Roma"),
    ("Bassi", "Gabriele", "Roma"),
    ("Bassi", "Matteo", "Roma"),
    ("Belluzzo", "Giorgio", "Roma"),
    ("Bergamini", "Andrea", "Roma"),
    ("Bersani", "Paolo", "Roma"),
    ("Bonavia", "Francesca", "Roma"),
    ("Brunelli", "Valeria", "Roma"),
    ("Buongiovanni", "Vincenzo", "Napoli"),
    ("Campaiola", "Carlo", "Roma"),
    ("Campisi", "Damiano", "Palermo"),
    ("Cavicchini", "Carlo", "Roma"),
    ("Celentano", "Eleonora", "Roma"),
    ("Cellini", "Sonia", "Cagliari"),
    ("Chiriaco'", "Vincenzo", "Roma"),
    ("Cicchetti", "Maria", "Roma"),
    ("Coccia", "Fabrizio", "Roma"),
    ("Corvino", "Michele", "Napoli"),
    ("Crescimanno", "Chiara", "Roma"),
    ("Cricenti", "Ileana", "Roma"),
    ("Criscuoli", "Ilaria", "Roma"),
    ("D'Acierno", "Anna Maria", "Napoli"),
    ("D'Alessandro", "Anna Rita", "Roma"),
    ("D'Angelo", "Angelo", "Roma"),
    ("De Cesaris", "Giuseppe", "Roma"),
    ("De Filippo", "Domenica", "Roma"),
    ("De Marco", "Matteo", "Roma"),
    ("De Simone", "Massimiliano", "Roma"),
    ("Del Forno", "Eugenio", "Napoli"),
    ("Della Martora", "Monica", "Roma"),
    ("D'Errico", "Vittorio", "Roma"),
    ("Di Falco", "Dario", "Milano"),
    ("D'Urso", "Graziano", "Palermo"),
    ("Escalar", "Adalgisa", "Roma"),
    ("Esteri", "Alessandra", "Roma"),
    ("Faggioli", "Simona", "Roma"),
    ("Faiola", "Lucio", "Roma"),
    ("Falconi", "Marco", "Roma"),
    ("Ferraro", "Elisabetta", "Roma"),
    ("Filardi", "Biagio", "Roma"),
    ("Filocamo", "Fabio", "Roma"),
    ("Fiore", "Stefania", "Potenza"),
    ("Forges", "Stefano", "Roma"),
    ("Franco", "Anniry", "Roma"),
    ("Gagliardi", "Teresa", "Roma"),
    ("Giovannelli", "Valentina", "Roma"),
    ("Giovanniello", "Carmela", "Napoli"),
    ("Giuliani", "Nicola", "Roma"),
    ("Gracco", "Marina", "Milano"),
    ("Graziano", "Ciro", "Napoli"),
    ("Greco", "Lucia", "Roma"),
    ("Grienti", "Giada", "Roma"),
    ("Guerra", "Stefania", "Roma"),
    ("Ietto", "Alessandra", "Roma"),
    ("Ioli", "Cesidia", "Roma"),
    ("Ioni", "Stefano", "Roma"),
    ("Juvara", "Alessandra", "Roma"),
    ("La Scaleia", "Ettore", "Roma"),
    ("Lancieri", "Luca", "Roma"),
    ("Laurora", "Zuleika", "Roma"),
    ("Leone", "Federica", "Roma"),
    ("Lironi", "Francesca", "Milano"),
    ("Lissoni", "Michela", "Milano"),
    ("Loic", "Jounko", "Milano"),
    ("Luciani", "Domenico", "Roma"),
    ("Madio", "Andrea", "Roma"),
    ("Maisto", "Angela", "Napoli"),
    ("Maka", "Agnese", "Roma"),
    ("Mamolo", "Angelo", "Milano"),
    ("Mancini", "Elda", "Roma"),
    ("Manna", "Margherita", "Napoli"),
    ("Marano", "Massimo", "Napoli"),
    ("Marzio", "Federica", "Napoli"),
    ("Masi", "Francesco", "Roma"),
    ("Mastropierro", "Leo", "Roma"),
    ("Materazzetti", "Alessandro", "Roma"),
    ("Materazzetti", "Amedeo", "Roma"),
    ("Maviglio", "Manuela", "Roma"),
    ("Melinelli", "Valeria", "Roma"),
    ("Mistone", "Paolo", "Napoli"),
    ("Nastri", "Gennario", "Napoli"),
    ("Pantano", "Antonella", "Roma"),
    ("Peirce", "Gianluca", "Roma"),
    ("Poliseno", "Andrea", "Napoli"),
    ("Prestifilippo", "Paolo", "Roma"),
    ("Punzo", "Giovanna", "Napoli"),
    ("Renelli", "Stefania", "Roma"),
    ("Ricci", "Angelo", "Napoli"),
    ("Rocco", "Rita", "Roma"),
    ("Rodino'", "Ugo", "Napoli"),
    ("Rosa", "Francesca", "Roma"),
    ("Rossetti", "Barbara", "Roma"),
    ("Rotolo", "Carmen", "Napoli"),
    ("Rullo", "Anna", "Napoli"),
    ("Russo", "Paola", "Roma"),
    ("Salerno", "Alessandro", "Roma"),
    ("Salerno", "Vincenzo", "Roma"),
    ("Sanguinazzi", "Carlo", "Milano"),
    ("Sansonetti", "Francesco", "Roma"),
    ("Santarelli", "Annamaria", "Roma"),
    ("Scarfo", "Antonio", "Roma"),
    ("Scavone", "Giovanni", "Potenza"),
    ("Schettini", "Gabriele", "Roma"),
    ("Senzasono", "Claudia", "Roma"),
    ("Senzasono", "Luca", "Roma"),
    ("Sepe", "Giuseppe", "Napoli"),
    ("Serranti", "Valerio", "Roma"),
    ("Sica", "Amelia", "Roma"),
    ("Soccorsi", "Mauro", "Roma"),
    ("Spagnoli", "Federica", "Milano"),
    ("Stanzione", "Gabriella", "Napoli"),
    ("Strambone", "Alessandra", "Roma"),
    ("Strata", "Raffaella", "Perugia"),
    ("Taddei", "Antonio", "Potenza"),
    ("Tamai", "Carlo", "Roma"),
    ("Tamantini", "Rossella", "Roma"),
    ("Tomassetti", "Carmina", "Roma"),
    ("Trenta", "Dora", "Napoli"),
    ("Tretta", "Maura", "Roma"),
    ("Troccia", "Fabiana", "Roma"),
    ("Turella", "Chiara", "Roma"),
    ("Ubaldini", "Paolo", "Roma"),
    ("Valeri", "Gabriele", "Roma"),
    ("Zoanetti", "Sarah", "Milano"),
    ("Zangrilli", "Tiziana", "Roma"),
    ("Cotta Ramusino", "Martina", "Roma"),
    ("Marigliano", "Romina", "Napoli"),
    ("Petrone", "Francesca", "Napoli"),
    ("Greco", "Alessandro", "Roma"),
    ("Sartoretti", "Giulio", "Roma"),
    ("Mezzera", "Stefano", "Milano"),
    ("Corvo", "Lucia", "Roma"),
    ("Mignosi", "Marco", "Milano"),
]

# 4. Import with dedup
created = 0
skipped = 0
errors = 0
seen = set()

for last, first, city in people:
    key = (last.lower().strip(), first.lower().strip())
    
    # Skip duplicates within this list
    if key in seen:
        print(f"[SKIP-LIST] {last} {first} (duplicato nella lista)")
        skipped += 1
        continue
    seen.add(key)
    
    # Skip if already in DB
    if key in existing_set:
        print(f"[SKIP-DB] {last} {first} (gia presente)")
        skipped += 1
        continue
    
    site_id = site_map.get(city.lower())
    if not site_id:
        print(f"[!!] {last} {first}: sede '{city}' non trovata!")
        errors += 1
        continue
    
    body = {
        "first_name": first,
        "last_name": last,
        "site_id": site_id,
        "is_active": True
    }
    
    try:
        r = api_post('/api/people', body)
        print(f"[OK] {last} {first} -> id={r['id']} (sede: {city})")
        created += 1
    except Exception as e:
        print(f"[!!] {last} {first}: {e}")
        errors += 1

print(f"\n{'='*50}")
print(f"Creati: {created}")
print(f"Saltati (duplicati): {skipped}")
print(f"Errori: {errors}")
print(f"Totale processati: {created + skipped + errors}")
