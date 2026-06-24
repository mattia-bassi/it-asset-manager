import json, urllib.request, urllib.parse, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

data = urllib.parse.urlencode({'username':'admin','password':'Admin_2025!!'}).encode()
req = urllib.request.Request('https://localhost:8000/api/auth/login', data=data, method='POST')
req.add_header('Content-Type','application/x-www-form-urlencoded')
token = json.loads(urllib.request.urlopen(req, context=ctx).read())['access_token']

asset = {
    "asset_code": "NB-PF2SR8XD",
    "serial_number": "PF2SR8XD",
    "manufacturer": "Lenovo",
    "model": "ThinkPad T14 Gen 1",
    "asset_type_id": 4,
    "site_id": 1,
    "status": "disponibile",
    "is_active": True
}

body = json.dumps(asset).encode()
req = urllib.request.Request('https://localhost:8000/api/assets', data=body, method='POST')
req.add_header('Authorization', 'Bearer ' + token)
req.add_header('Content-Type', 'application/json')

try:
    resp = urllib.request.urlopen(req, context=ctx)
    r = json.loads(resp.read())
    print(f"[OK] Asset creato: id={r['id']} code={r['asset_code']} sn={r['serial_number']}")
except urllib.error.HTTPError as e:
    print(f"[!!] Errore {e.code}: {e.read().decode()}")
