#!/usr/bin/env python3
"""
Compliance Test Suite - IT Asset Manager v2.7.5
External container — ISO 27001:2022 / GDPR verification.

Runs 26 tests against the app via HTTP from a separate container.
Generates JSON + PDF reports in /app/reports/.
"""

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
APP_URL = os.environ.get("APP_URL", "http://localhost:8000").rstrip("/")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin")
REPORT_DIR = Path(os.environ.get("REPORT_DIR", "/app/reports"))
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# SSL context — only used when APP_URL is https
SSL_CTX = None
if APP_URL.startswith("https"):
    SSL_CTX = ssl.create_default_context()
    SSL_CTX.check_hostname = False
    SSL_CTX.verify_mode = ssl.CERT_NONE

# Results accumulator
results = {"passed": 0, "failed": 0, "tests": []}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def log_test(category: str, name: str, passed: bool, detail: str = ""):
    """Record a single test result."""
    status = "PASS" if passed else "FAIL"
    results["passed" if passed else "failed"] += 1
    results["tests"].append({
        "category": category,
        "name": name,
        "status": status,
        "detail": detail,
    })
    icon = "\u2705" if passed else "\u274c"
    suffix = f" \u2014 {detail}" if detail else ""
    print(f"  {icon} {name}{suffix}")


def api_request(path: str, method: str = "GET", data=None, token=None):
    """HTTP request helper with proper error handling."""
    url = f"{APP_URL}{path}"
    if data and isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=data, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if method in ("PUT", "POST") and not data:
        req.add_header("Content-Type", "application/json")
        req.data = b"{}"
    req.add_header("Connection", "close")
    try:
        resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=15)
        ct = resp.headers.get("content-type", "")
        body = json.loads(resp.read()) if ct.startswith("application/json") else resp.read()
        return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return e.code, body, dict(e.headers)
    except Exception as e:
        return 0, str(e), {}


def get_token() -> str:
    """Authenticate and return JWT token."""
    data = urllib.parse.urlencode({
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD,
    }).encode()
    req = urllib.request.Request(f"{APP_URL}/api/auth/login", data=data)
    req.add_header("Connection", "close")
    resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=15)
    return json.loads(resp.read())["access_token"]


def wait_for_app(max_retries: int = 10, delay: int = 3) -> bool:
    """Wait for the app to be reachable before running tests."""
    print(f"\n\u23f3 Waiting for app at {APP_URL} ...")
    for i in range(max_retries):
        try:
            req = urllib.request.Request(f"{APP_URL}/api/health")
            req.add_header("Connection", "close")
            resp = urllib.request.urlopen(req, context=SSL_CTX, timeout=5)
            if resp.status == 200:
                print(f"  App reachable (attempt {i + 1})")
                return True
        except Exception:
            pass
        time.sleep(delay)
    print(f"  App NOT reachable after {max_retries * delay}s")
    return False


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------
CAT_HTTPS = "HTTPS/TLS"
CAT_HEADERS = "Security Headers"
CAT_RATE = "Rate Limiting"
CAT_AUTH = "Autenticazione"
CAT_GDPR = "GDPR"
CAT_AUDIT = "Audit Log"
CAT_ENCRYPT = "Encryption"
CAT_ROTATE = "Log Rotation"
CAT_DB = "Database Hardening"


# ---------------------------------------------------------------------------
# Test 1: HTTPS / TLS
# ---------------------------------------------------------------------------
def test_https():
    print(f"\n\U0001f512 TEST HTTPS / TLS")
    status, _, _ = api_request("/api/health")
    is_https = APP_URL.startswith("https")
    log_test(CAT_HTTPS, "HTTPS connessione attiva", is_https and status == 200,
             "" if is_https else "App running on HTTP")


# ---------------------------------------------------------------------------
# Test 2-7: Security Headers
# ---------------------------------------------------------------------------
def test_security_headers():
    print(f"\n\U0001f6e1\ufe0f TEST SECURITY HEADERS (OWASP)")
    status, _, headers = api_request("/api/health")
    if status == 0:
        for name in ["Header x-content-type-options", "Header x-frame-options",
                      "Header x-xss-protection", "Header referrer-policy",
                      "Content-Security-Policy presente", "Permissions-Policy presente"]:
            log_test(CAT_HEADERS, name, False, "App not reachable")
        return

    h_lower = {k.lower(): v for k, v in headers.items()}
    expected = {
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "x-xss-protection": "1; mode=block",
        "referrer-policy": "strict-origin-when-cross-origin",
    }
    for header, value in expected.items():
        found = h_lower.get(header, "")
        log_test(CAT_HEADERS, f"Header {header}", value in found, f"found: {str(found)[:50]}")
    log_test(CAT_HEADERS, "Content-Security-Policy presente", "content-security-policy" in h_lower)
    log_test(CAT_HEADERS, "Permissions-Policy presente", "permissions-policy" in h_lower)


# ---------------------------------------------------------------------------
# Test 8: Rate Limiting
# ---------------------------------------------------------------------------
def test_rate_limiting():
    print(f"\n\u23f1\ufe0f TEST RATE LIMITING")
    blocked = False
    for i in range(6):
        status, _, _ = api_request("/api/auth/login", method="POST",
                                   data={"username": "fakeuser", "password": "fakepass"})
        if status == 429:
            blocked = True
            log_test(CAT_RATE, f"Rate limit attivato al tentativo {i + 1}", True)
            break
    if not blocked:
        log_test(CAT_RATE, "Rate limit attivato entro 6 tentativi", False, "429 mai ricevuto")
    # Wait for rate limit reset before auth tests
    print("  Attesa 61s per reset rate limiter...")
    time.sleep(61)


# ---------------------------------------------------------------------------
# Test 9-11: Authentication
# ---------------------------------------------------------------------------
def test_authentication():
    print(f"\n\U0001f511 TEST AUTENTICAZIONE")
    # 9. Valid login
    status, body, _ = api_request("/api/auth/login", method="POST",
                                  data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD})
    log_test(CAT_AUTH, "Login admin valido",
             status == 200 and isinstance(body, dict) and "access_token" in body)
    # 10. Invalid login
    status, _, _ = api_request("/api/auth/login", method="POST",
                               data={"username": "admin", "password": "wrongpass"})
    log_test(CAT_AUTH, "Login password errata rifiutato", status == 401)
    # 11. No token
    status, _, _ = api_request("/api/audit-logs/")
    log_test(CAT_AUTH, "Accesso senza token rifiutato", status in (401, 403))


# ---------------------------------------------------------------------------
# Test 12-16: GDPR Endpoints
# ---------------------------------------------------------------------------
def test_gdpr_endpoints(token: str):
    print(f"\n\U0001f4cb TEST ENDPOINT GDPR (Art. 15-22)")
    # 12. Art. 15
    status, _, _ = api_request("/api/gdpr/my-data", token=token)
    log_test(CAT_GDPR, "GET /api/gdpr/my-data (Art. 15)", status == 200)
    # 13. Art. 20
    status, _, _ = api_request("/api/gdpr/data-portability", token=token)
    log_test(CAT_GDPR, "GET /api/gdpr/data-portability (Art. 20)", status == 200)
    # 14. Art. 17
    status, _, _ = api_request("/api/gdpr/erasure", method="DELETE", token=token)
    log_test(CAT_GDPR, "DELETE /api/gdpr/erasure (Art. 17) raggiungibile", status in (200, 422, 400))
    # 15. Art. 16
    status, _, _ = api_request("/api/gdpr/rectification", method="PUT", token=token)
    log_test(CAT_GDPR, "PUT /api/gdpr/rectification (Art. 16) raggiungibile", status in (200, 422, 400))
    # 16. Art. 18
    status, _, _ = api_request("/api/gdpr/restriction", method="POST", token=token)
    log_test(CAT_GDPR, "POST /api/gdpr/restriction (Art. 18) raggiungibile", status in (200, 422, 400))


# ---------------------------------------------------------------------------
# Test 17-19: Audit Log
# ---------------------------------------------------------------------------
def test_audit_log(token: str):
    print(f"\n\U0001f4dd TEST AUDIT LOG")
    # 17. Endpoint works
    status, body, _ = api_request("/api/audit-logs/?limit=5", token=token)
    log_test(CAT_AUDIT, "GET /api/audit-logs funzionante", status == 200)
    # 18-19: conditional on success
    if status == 200 and isinstance(body, dict):
        total = body.get("total", 0)
        items = body.get("items", [])
        log_test(CAT_AUDIT, f"Audit logs presenti (totale: {total})", total > 0)
        if items:
            first = items[0]
            has_fields = all(k in first for k in ["id", "action", "entity_type", "created_at"])
            log_test(CAT_AUDIT, "Struttura log completa (id, action, entity_type, created_at)", has_fields)
        else:
            log_test(CAT_AUDIT, "Struttura log completa (id, action, entity_type, created_at)", False, "Nessun log presente")
    else:
        log_test(CAT_AUDIT, "Audit logs presenti", False, f"status={status}")
        log_test(CAT_AUDIT, "Struttura log completa (id, action, entity_type, created_at)", False, f"status={status}")


# ---------------------------------------------------------------------------
# Test 20-22: Encryption at Rest (via API endpoint)
# ---------------------------------------------------------------------------
def test_encryption(token: str):
    print(f"\n\U0001f510 TEST ENCRYPTION AT REST")
    status, body, _ = api_request("/api/compliance/encryption-check", token=token)
    if status == 200 and isinstance(body, dict):
        for t in body.get("tests", []):
            log_test(CAT_ENCRYPT, t["name"], t["passed"], t.get("detail", ""))
    else:
        log_test(CAT_ENCRYPT, "encrypt_log produce token Fernet", False, f"Endpoint error: status={status}")
        log_test(CAT_ENCRYPT, "decrypt_log ritorna plaintext", False, f"Endpoint error: status={status}")
        log_test(CAT_ENCRYPT, "Backward compat: plaintext ritornato invariato", False, f"Endpoint error: status={status}")


# ---------------------------------------------------------------------------
# Test 23-25: Log Rotation
# ---------------------------------------------------------------------------
def test_log_rotation(token: str):
    print(f"\n\U0001f504 TEST LOG ROTATION")
    # 23. Endpoint works
    status, body, _ = api_request("/api/audit-logs/rotate?retention_months=24", method="DELETE", token=token)
    log_test(CAT_ROTATE, "DELETE /api/audit-logs/rotate funzionante", status == 200)
    # 24-25: conditional on success
    if status == 200 and isinstance(body, dict):
        log_test(CAT_ROTATE, "Risposta contiene archived_count", "archived_count" in body)
        log_test(CAT_ROTATE, "Risposta contiene remaining_count", "remaining_count" in body)
    else:
        log_test(CAT_ROTATE, "Risposta contiene archived_count", False, f"status={status}")
        log_test(CAT_ROTATE, "Risposta contiene remaining_count", False, f"status={status}")


# ---------------------------------------------------------------------------
# Test 26: Database Hardening (via API endpoint)
# ---------------------------------------------------------------------------
def test_db_hardening(token: str):
    print(f"\n\U0001f5c4\ufe0f TEST DATABASE HARDENING")
    status, body, _ = api_request("/api/compliance/db-check", token=token)
    if status == 200 and isinstance(body, dict):
        log_test(CAT_DB, "Connessione DB da container app funzionante", body.get("connected", False),
                 body.get("detail", ""))
    else:
        log_test(CAT_DB, "Connessione DB da container app funzionante", False, f"Endpoint error: status={status}")


# ---------------------------------------------------------------------------
# PDF Report Generation
# ---------------------------------------------------------------------------
def sanitize_text(text: str) -> str:
    """Replace characters not supported by Helvetica (latin-1) in fpdf2."""
    known = {
        "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
        "\u201c": '"', "\u201d": '"', "\u2026": "...", "\u2022": "-",
        "\u2713": "OK", "\u2714": "OK", "\u2717": "NO", "\u2718": "NO",
        "\u2705": "[OK]", "\u274c": "[NO]",
    }
    for char, repl in known.items():
        text = text.replace(char, repl)
    return "".join(c for c in text if ord(c) < 256)


def generate_pdf(report: dict, output_path: Path):
    """Generate a professional compliance PDF report."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    class CompliancePDF(FPDF):
        def header(self):
            self.ln(10)

        def footer(self):
            self.set_y(-20)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Pagina {self.page_no()}", align="C")

    pdf = CompliancePDF()
    pdf.set_auto_page_break(auto=True, margin=25)

    gray = (81, 93, 100)
    green = (34, 197, 94)
    red = (239, 68, 68)
    yellow = (255, 221, 15)

    # Page 1 — Title
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(*gray)
    pdf.cell(0, 10, sanitize_text("REPORT CONFORMITA ISO 27001:2022"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, sanitize_text("IT Asset Management System"), align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    dt_str = report.get("date", datetime.now().isoformat())
    try:
        dt_obj = datetime.fromisoformat(dt_str)
        exec_str = dt_obj.strftime("%d/%m/%Y %H:%M")
    except Exception:
        exec_str = dt_str[:19].replace("T", " ")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, sanitize_text(f"Data esecuzione: {exec_str}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, sanitize_text(f"Operatore: {ADMIN_USERNAME}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, sanitize_text(f"Versione sistema: {report.get('version', '2.7.5')}"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)

    passed = report.get("passed", 0)
    total = report.get("total_tests", 0)
    is_ok = report.get("failed", 1) == 0
    pdf.set_fill_color(*(green if is_ok else red))
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, sanitize_text(f"Risultato: {passed}/{total} test superati"), fill=True, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.set_text_color(*gray)

    # Group by category
    tests = report.get("tests", [])
    by_cat: dict[str, list] = {}
    for t in tests:
        cat = t.get("category", "Altro")
        by_cat.setdefault(cat, []).append(t)

    for category, cat_tests in by_cat.items():
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(*yellow)
        pdf.set_text_color(*gray)
        pdf.cell(0, 8, sanitize_text(category), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(3)

        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(*gray)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(110, 7, "Nome", border=1, fill=True)
        pdf.cell(20, 7, "Stato", border=1, fill=True, align="C")
        pdf.cell(60, 7, "Dettaglio", border=1, fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for t in cat_tests:
            is_pass = t.get("status") == "PASS"
            pdf.set_text_color(*(green if is_pass else red))
            pdf.cell(110, 6, sanitize_text(t.get("name", "")[:65]), border=1)
            pdf.cell(20, 6, sanitize_text("OK" if is_pass else "NO"), border=1, align="C")
            pdf.set_text_color(*gray)
            pdf.cell(60, 6, sanitize_text((t.get("detail", "") or "-")[:50]), border=1)
            pdf.ln()
        pdf.ln(5)

    # Last page — Approval
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(*yellow)
    pdf.set_text_color(*gray)
    pdf.cell(0, 8, sanitize_text("APPROVAZIONE"), fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, sanitize_text("Data: ___/___/______"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.cell(0, 7, sanitize_text("Firma Responsabile IT: _______________________"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.cell(0, 7, sanitize_text("Firma Direzione: _______________________"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 6, sanitize_text("Documento generato automaticamente dal sistema IT Asset Manager"), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.output(str(output_path))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    now = datetime.now()

    print("=" * 60)
    print("\U0001f3e2 COMPLIANCE TEST SUITE \u2014 IT Asset Manager v2.7.5")
    print(f"\U0001f4c5 Data: {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"\U0001f310 Target: {APP_URL}")
    print(f"\U0001f464 Admin: {ADMIN_USERNAME}")
    print("=" * 60)

    # Wait for app
    if not wait_for_app():
        print("\n\u274c App non raggiungibile. Abort.")
        sys.exit(2)

    # Run all tests
    test_https()
    test_security_headers()
    test_rate_limiting()
    test_authentication()

    # Get token for authenticated tests
    token = None
    try:
        token = get_token()
    except Exception as e:
        print(f"\n\u274c Impossibile ottenere token: {e}")

    if token:
        test_gdpr_endpoints(token)
        test_audit_log(token)
        test_encryption(token)
        test_log_rotation(token)
        test_db_hardening(token)
    else:
        # Log all authenticated tests as failed
        for name in [
            "GET /api/gdpr/my-data (Art. 15)",
            "GET /api/gdpr/data-portability (Art. 20)",
            "DELETE /api/gdpr/erasure (Art. 17) raggiungibile",
            "PUT /api/gdpr/rectification (Art. 16) raggiungibile",
            "POST /api/gdpr/restriction (Art. 18) raggiungibile",
        ]:
            log_test(CAT_GDPR, name, False, "Token non ottenuto")
        log_test(CAT_AUDIT, "GET /api/audit-logs funzionante", False, "Token non ottenuto")
        log_test(CAT_AUDIT, "Audit logs presenti", False, "Token non ottenuto")
        log_test(CAT_AUDIT, "Struttura log completa (id, action, entity_type, created_at)", False, "Token non ottenuto")
        log_test(CAT_ENCRYPT, "encrypt_log produce token Fernet", False, "Token non ottenuto")
        log_test(CAT_ENCRYPT, "decrypt_log ritorna plaintext", False, "Token non ottenuto")
        log_test(CAT_ENCRYPT, "Backward compat: plaintext ritornato invariato", False, "Token non ottenuto")
        log_test(CAT_ROTATE, "DELETE /api/audit-logs/rotate funzionante", False, "Token non ottenuto")
        log_test(CAT_ROTATE, "Risposta contiene archived_count", False, "Token non ottenuto")
        log_test(CAT_ROTATE, "Risposta contiene remaining_count", False, "Token non ottenuto")
        log_test(CAT_DB, "Connessione DB da container app funzionante", False, "Token non ottenuto")

    # Build report
    total = results["passed"] + results["failed"]
    report = {
        "date": now.isoformat(),
        "version": "2.7.5",
        "app_url": APP_URL,
        "operator": ADMIN_USERNAME,
        "total_tests": total,
        "passed": results["passed"],
        "failed": results["failed"],
        "compliance_status": "CONFORME" if results["failed"] == 0 else "NON CONFORME",
        "tests": results["tests"],
    }

    # Summary
    print("\n" + "=" * 60)
    print(f"\U0001f4ca RISULTATI: {results['passed']}/{total} test superati")
    if results["failed"] == 0:
        print("\u2705 TUTTI I TEST SUPERATI \u2014 SISTEMA CONFORME")
    else:
        print(f"\u274c {results['failed']} TEST FALLITI \u2014 VERIFICARE")
        for t in results["tests"]:
            if t["status"] == "FAIL":
                print(f"   \u26a0\ufe0f {t['name']}: {t['detail']}")
    print("=" * 60)

    # Save JSON report
    json_path = REPORT_DIR / "compliance_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n\U0001f4c4 JSON report: {json_path}")

    # Save latest copy (for app UI to read)
    latest_path = REPORT_DIR / "latest_report.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Generate PDF
    try:
        pdf_filename = f"compliance_report_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = REPORT_DIR / pdf_filename
        generate_pdf(report, pdf_path)
        print(f"\U0001f4c4 PDF report: {pdf_path}")
    except Exception as e:
        print(f"\u26a0\ufe0f PDF generation failed: {e}")

    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
