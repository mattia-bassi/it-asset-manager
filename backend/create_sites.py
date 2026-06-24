import json, urllib.request, urllib.parse, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

data = urllib.parse.urlencode({'username':'admin','password':'Admin_2025!!'}).encode()
req = urllib.request.Request('https://localhost:8000/api/auth/login', data=data, method='POST')
req.add_header('Content-Type','application/x-www-form-urlencoded')
token = json.loads(urllib.request.urlopen(req, context=ctx).read())['access_token']

sedi = [
    {'name':'Napoli','address':'Piazza Giovanni Bovio, 22','city':'Napoli','zip_code':'80133','country':'Italia','phone':'+39 081 4206442'},
    {'name':'Perugia','address':'Via Mario Angeloni, 80/B','city':'Perugia','zip_code':'06124','country':'Italia','phone':''},
    {'name':'Palermo','address':'','city':'Palermo','zip_code':'','country':'Italia','phone':''},
    {'name':'Cagliari','address':'','city':'Cagliari','zip_code':'','country':'Italia','phone':''},
    {'name':'Potenza','address':'','city':'Potenza','zip_code':'','country':'Italia','phone':''},
]

for s in sedi:
    body = json.dumps(s).encode()
    req = urllib.request.Request('https://localhost:8000/api/sites', data=body, method='POST')
    req.add_header('Authorization','Bearer '+token)
    req.add_header('Content-Type','application/json')
    try:
        resp = urllib.request.urlopen(req, context=ctx)
        r = json.loads(resp.read())
        print(f"[OK] {s['name']} -> id={r['id']}")
    except Exception as e:
        print(f"[!!] {s['name']}: {e}")
