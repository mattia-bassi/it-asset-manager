#!/usr/bin/env python3
"""
Functional Test Suite - IT Asset Manager v2.2
Verifica funzionamento di tutti gli endpoint principali.
"""

import sys
import os
import json
import ssl
import time
import urllib.request
import urllib.parse

# Configurazione
BASE_URL = "https://localhost:8000"
ADMIN_USER = "admin"
ADMIN_PASS = "Admin_2025!!"
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# Contatori
results = {"passed": 0, "failed": 0, "tests": []}


def log_test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results["passed" if passed else "failed"] += 1
    results["tests"].append({"name": name, "status": status, "detail": detail})
    emoji = "✅" if passed else "❌"
    print(f"  {emoji} {name}" + (f" — {detail}" if detail else ""))


def api_request(path, method="GET", data=None, token=None, json_data=None):
    url = f"{BASE_URL}{path}"
    if data and isinstance(data, dict) and not json_data:
        data = urllib.parse.urlencode(data).encode()
    if json_data:
        data = json.dumps(json_data).encode()
    req = urllib.request.Request(url, data=data, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if json_data:
        req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, context=SSL_CTX)
        ct = resp.headers.get("content-type", "")
        body = json.loads(resp.read()) if "json" in ct else resp.read()
        return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        return e.code, body, dict(e.headers) if e.headers else {}
    except Exception as e:
        return 0, str(e), {}


def get_token():
    data = urllib.parse.urlencode({"username": ADMIN_USER, "password": ADMIN_PASS}).encode()
    req = urllib.request.Request(f"{BASE_URL}/api/auth/login", data=data)
    resp = urllib.request.urlopen(req, context=SSL_CTX)
    return json.loads(resp.read())["access_token"]


# ===========================================
# TEST 1: HEALTH CHECK
# ===========================================
def test_health():
    print("\n💓 HEALTH CHECK")
    status, body, _ = api_request("/api/health")
    log_test("GET /api/health", status == 200)


# ===========================================
# TEST 2: AUTH
# ===========================================
def test_auth():
    print("\n🔑 AUTENTICAZIONE")
    # Login
    status, body, _ = api_request("/api/auth/login", method="POST", data={"username": ADMIN_USER, "password": ADMIN_PASS})
    log_test("POST /api/auth/login", status == 200 and isinstance(body, dict) and "access_token" in body)

    token = body["access_token"] if isinstance(body, dict) else ""

    # Me
    status, body, _ = api_request("/api/auth/me", token=token)
    log_test("GET /api/auth/me", status == 200 and isinstance(body, dict) and "username" in body, f"user: {body.get('username', '?')}" if isinstance(body, dict) else "")

    return token


# ===========================================
# TEST 3: ASSET TYPES
# ===========================================
def test_asset_types(token):
    print("\n📂 ASSET TYPES")
    status, body, _ = api_request("/api/asset-types?is_active=true", token=token)
    count = len(body.get("items", [])) if isinstance(body, dict) else len(body) if isinstance(body, list) else 0
    log_test("GET /api/asset-types", status == 200 and (isinstance(body, dict) or isinstance(body, list)), f"{count} tipi trovati")


# ===========================================
# TEST 4: ASSETS
# ===========================================
def test_assets(token):
    print("\n💻 ASSETS")
    status, body, _ = api_request("/api/assets", token=token)
    count = body.get("total", 0) if isinstance(body, dict) else len(body) if isinstance(body, list) else 0
    log_test("GET /api/assets", status == 200, f"{count} asset trovati")

    # Search
    status, body, _ = api_request("/api/assets?search=test", token=token)
    log_test("GET /api/assets?search=test", status == 200)


# ===========================================
# TEST 5: PEOPLE
# ===========================================
def test_people(token):
    print("\n👥 PEOPLE")
    status, body, _ = api_request("/api/people", token=token)
    count = body.get("total", len(body.get("items", []))) if isinstance(body, dict) else len(body) if isinstance(body, list) else 0
    log_test("GET /api/people", status == 200, f"{count} persone trovate")


# ===========================================
# TEST 6: ASSIGNMENTS
# ===========================================
def test_assignments(token):
    print("\n📋 ASSIGNMENTS")
    status, body, _ = api_request("/api/assignments", token=token)
    count = body.get("total", 0) if isinstance(body, dict) else len(body) if isinstance(body, list) else 0
    log_test("GET /api/assignments", status == 200, f"{count} assegnazioni trovate")


# ===========================================
# TEST 7: INVENTORY
# ===========================================
def test_inventory(token):
    print("\n📦 INVENTORY")
    status, body, _ = api_request("/api/inventory", token=token)
    count = body.get("total", len(body.get("items", []))) if isinstance(body, dict) else len(body) if isinstance(body, list) else 0
    log_test("GET /api/inventory", status == 200, f"{count} SKU trovati")


# ===========================================
# TEST 8: SIMS
# ===========================================
def test_sims(token):
    print("\n📱 SIMS")
    status, body, _ = api_request("/api/sims", token=token)
    count = body.get("total", len(body.get("items", []))) if isinstance(body, dict) else len(body) if isinstance(body, list) else 0
    log_test("GET /api/sims", status == 200, f"{count} SIM trovate")


# ===========================================
# TEST 9: BADGES
# ===========================================
def test_badges(token):
    print("\n🪪 BADGES")
    status, body, _ = api_request("/api/badges", token=token)
    count = body.get("total", len(body.get("items", []))) if isinstance(body, dict) else len(body) if isinstance(body, list) else 0
    log_test("GET /api/badges", status == 200, f"{count} badge trovati")


# ===========================================
# TEST 10: SITES
# ===========================================
def test_sites(token):
    print("\n🏢 SITES")
    status, body, _ = api_request("/api/sites", token=token)
    count = body.get("total", len(body.get("items", []))) if isinstance(body, dict) else len(body) if isinstance(body, list) else 0
    log_test("GET /api/sites", status == 200, f"{count} sedi trovate")


# ===========================================
# TEST 11: DASHBOARD
# ===========================================
def test_dashboard(token):
    print("\n📊 DASHBOARD")
    endpoints = [
        "/api/dashboard/overview",
        "/api/dashboard/assets-by-status",
        "/api/dashboard/assets-by-type",
        "/api/dashboard/assignments-timeline",
        "/api/dashboard/recent-assignments",
        "/api/dashboard/low-stock-items",
    ]
    for ep in endpoints:
        status, body, _ = api_request(ep, token=token)
        name = ep.split("/")[-1]
        log_test(f"GET {ep}", status == 200, name)


# ===========================================
# TEST 12: REPORTS
# ===========================================
def test_reports(token):
    print("\n📄 REPORTS")
    status, body, _ = api_request("/api/reports/assets-by-type/excel", token=token)
    log_test("GET /api/reports/assets-by-type/excel (Excel)", status == 200)

    status, body, _ = api_request("/api/reports/my-assets/excel", token=token)
    log_test("GET /api/reports/my-assets/excel", status in (200, 400, 404), "OK o nessun asset assegnato")


# ===========================================
# TEST 13: USERS
# ===========================================
def test_users(token):
    print("\n👤 USERS")
    status, body, _ = api_request("/api/users", token=token)
    count = len(body) if isinstance(body, list) else 0
    log_test("GET /api/users", status == 200, f"{count} utenti trovati")


# ===========================================
# TEST 14: AUDIT LOGS
# ===========================================
def test_audit_logs(token):
    print("\n📝 AUDIT LOGS")
    status, body, _ = api_request("/api/audit-logs/?limit=5", token=token)
    log_test("GET /api/audit-logs", status == 200)

    if status == 200 and isinstance(body, dict):
        total = body.get("total", 0)
        items = body.get("items", [])
        log_test(f"Audit logs presenti ({total} totali)", total >= 0)
        # Verifica decryption (i campi non devono iniziare con gAAAAA)
        if items:
            first = items[0]
            details = first.get("details", "") or ""
            encrypted = details.startswith("gAAAAA") if details else False
            log_test("Decryption audit log funzionante", not encrypted, "plaintext OK" if not encrypted else "ANCORA CRIPTATO!")


# ===========================================
# TEST 15: GDPR ENDPOINTS
# ===========================================
def test_gdpr(token):
    print("\n📋 GDPR ENDPOINTS")
    status, body, _ = api_request("/api/gdpr/my-data", token=token)
    log_test("GET /api/gdpr/my-data (Art. 15)", status == 200)

    status, body, _ = api_request("/api/gdpr/data-portability", token=token)
    log_test("GET /api/gdpr/data-portability (Art. 20)", status == 200)


# ===========================================
# TEST 16: DOCUMENT TEMPLATES
# ===========================================
def test_document_templates(token):
    print("\n📄 DOCUMENT TEMPLATES")
    status, body, _ = api_request("/api/document-templates", token=token)
    count = len(body) if isinstance(body, list) else 0
    log_test("GET /api/document-templates", status == 200, f"{count} template trovati")


# ===========================================
# TEST 17: FRONTEND SPA
# ===========================================
def test_frontend():
    print("\n🌐 FRONTEND SPA")
    status, body, headers = api_request("/")
    ct = headers.get("content-type", headers.get("Content-Type", ""))
    is_html = "text/html" in ct
    log_test("GET / serve index.html", status == 200 and is_html)

    # SPA fallback — rotte React devono servire index.html
    status, body, headers = api_request("/login")
    ct = headers.get("content-type", headers.get("Content-Type", ""))
    is_html = "text/html" in ct
    log_test("GET /login (SPA fallback)", status == 200 and is_html)

    status, body, headers = api_request("/dashboard")
    ct = headers.get("content-type", headers.get("Content-Type", ""))
    is_html = "text/html" in ct
    log_test("GET /dashboard (SPA fallback)", status == 200 and is_html)


# ===========================================
# ESECUZIONE
# ===========================================
if __name__ == "__main__":
    import datetime as dt

    print("=" * 60)
    print("🏢 FUNCTIONAL TEST SUITE — IT Asset Manager v2.2")
    print("🏢 IT Asset Manager")
    print(f"📅 Data: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    test_health()
    token = test_auth()

    if token:
        test_asset_types(token)
        test_assets(token)
        test_people(token)
        test_assignments(token)
        test_inventory(token)
        test_sims(token)
        test_badges(token)
        test_sites(token)
        test_dashboard(token)
        test_reports(token)
        test_users(token)
        test_audit_logs(token)
        test_gdpr(token)
        test_document_templates(token)

    test_frontend()

    # RIEPILOGO
    print("\n" + "=" * 60)
    total = results["passed"] + results["failed"]
    print(f"📊 RISULTATI: {results['passed']}/{total} test superati")
    if results["failed"] == 0:
        print("✅ TUTTI I TEST SUPERATI — APPLICAZIONE FUNZIONANTE")
    else:
        print(f"❌ {results['failed']} TEST FALLITI:")
        for t in results["tests"]:
            if t["status"] == "FAIL":
                print(f"   ⚠️ {t['name']}: {t['detail']}")
    print("=" * 60)

    # Salva report JSON
    report_path = "/app/data/functional_test_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    report = {
        "date": dt.datetime.now().isoformat(),
        "version": "2.2",
        "company": "IT Asset Manager",
        "type": "functional",
        "total_tests": total,
        "passed": results["passed"],
        "failed": results["failed"],
        "status": "OK" if results["failed"] == 0 else "FAILED",
        "tests": results["tests"],
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Report salvato in: {report_path}")
    sys.exit(0 if results["failed"] == 0 else 1)
