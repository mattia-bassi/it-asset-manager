import base64
import datetime
import hashlib
import ipaddress
import json
import os
import re
import secrets
import subprocess
import threading
import time
from functools import wraps
from flask import Flask, render_template, jsonify, request
from schema_ddl import LEVEL_0_TABLES, LEVEL_1_TABLES, LEVEL_2_TABLES, LEVEL_3_TABLES, ALEMBIC_VERSION_TABLE, ALEMBIC_HEAD

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# --- Configuration ---
SETUP_USERNAME = "setup"
SETUP_PASSWORD = "Setup@FirstRun!"
SESSION_TIMEOUT = 3600  # 60 minutes
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutes
PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "/project")

# --- State ---
active_tokens = {}
login_attempts = {"count": 0, "locked_until": 0}
last_config_content = None  # Stores generated config for download

install_state = {
    "current_step": 0,
    "data": None,
    "completed": [],
    "debug_log": []
}


def debug_log(msg):
    """Append a timestamped message to the debug log."""
    entry = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}"
    install_state["debug_log"].append(entry)
    print(f"[DEBUG] {entry}")


def create_ddl_tables(tables_dict, db_name, root_password):
    """Execute DDL statements via docker exec mysql stdin.
    Drops existing tables first to avoid InnoDB tablespace conflicts (errno 184).
    Returns (success: bool, created_tables: list, error_msg: str|None).
    """
    created = []
    for table_name, ddl in tables_dict.items():
        # Drop table if exists (clears orphaned InnoDB tablespace)
        drop_sql = f"SET FOREIGN_KEY_CHECKS=0; DROP TABLE IF EXISTS `{table_name}`; SET FOREIGN_KEY_CHECKS=1;"
        subprocess.run(
            ["docker", "exec", "-e", f"MYSQL_PWD={root_password}",
             "asset-mariadb", "mysql", "-uroot", db_name, "-e", drop_sql],
            capture_output=True, text=True, timeout=15
        )

        # Create table
        result = subprocess.run(
            ["docker", "exec", "-i", "-e", f"MYSQL_PWD={root_password}",
             "asset-mariadb", "mysql", "-uroot", db_name],
            input=ddl,
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return False, created, f"CREATE TABLE {table_name} FAILED: {result.stderr.strip()}"
        debug_log(f"Created table: {table_name}")
        created.append(table_name)
    return True, created, None


def detect_host_project_path():
    """Detect the actual host path of /project by inspecting the wizard container's mounts."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "asset-setup-wizard", "--format",
             "{{range .Mounts}}{{if eq .Destination \"/project\"}}{{.Source}}{{end}}{{end}}"],
            capture_output=True, text=True, timeout=10
        )
        host_path = result.stdout.strip()
        if host_path and os.path.isabs(host_path):
            debug_log(f"Detected host project path: {host_path}")
            return host_path
    except Exception as e:
        debug_log(f"Failed to detect host path: {e}")
    # Fallback: use PROJECT_ROOT
    debug_log(f"Using fallback PROJECT_ROOT: {PROJECT_ROOT}")
    return PROJECT_ROOT


# ══════════════════════════════════════════════════════════════
#  AUTH HELPERS
# ══════════════════════════════════════════════════════════════

def generate_token():
    token = secrets.token_urlsafe(48)
    active_tokens[token] = time.time()
    return token


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth_header[7:]
        if token not in active_tokens:
            return jsonify({"error": "Invalid token"}), 401
        if time.time() - active_tokens[token] > SESSION_TIMEOUT:
            del active_tokens[token]
            return jsonify({"error": "Session expired"}), 401
        return f(*args, **kwargs)
    return decorated


# ══════════════════════════════════════════════════════════════
#  PAGE ROUTES
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "setup-wizard"})


@app.route("/api/login", methods=["POST"])
def api_login():
    now = time.time()

    if login_attempts["locked_until"] > now:
        remaining = int(login_attempts["locked_until"] - now)
        return jsonify({"error": "Too many attempts", "retry_after": remaining}), 429

    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if username == SETUP_USERNAME and password == SETUP_PASSWORD:
        login_attempts["count"] = 0
        token = generate_token()
        return jsonify({"token": token})
    else:
        login_attempts["count"] += 1
        if login_attempts["count"] >= MAX_LOGIN_ATTEMPTS:
            login_attempts["locked_until"] = now + LOCKOUT_DURATION
            login_attempts["count"] = 0
            return jsonify({"error": "Too many attempts", "retry_after": LOCKOUT_DURATION}), 429
        return jsonify({"error": "Invalid credentials"}), 401


# ══════════════════════════════════════════════════════════════
#  NETWORK DETECTION
# ══════════════════════════════════════════════════════════════

def detect_network_info():
    """Detect network interface, subnet and gateway from host."""
    result = {"interface": None, "subnet": None, "gateway": None, "suggested_ips": []}

    try:
        gw_output = subprocess.run(
            ["ip", "route", "show", "default"],
            capture_output=True, text=True, timeout=5
        )
        match = re.search(r"default via (\S+) dev (\S+)", gw_output.stdout)
        if match:
            result["gateway"] = match.group(1)
            result["interface"] = match.group(2)

        if result["interface"]:
            addr_output = subprocess.run(
                ["ip", "-4", "addr", "show", result["interface"]],
                capture_output=True, text=True, timeout=5
            )
            match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", addr_output.stdout)
            if match:
                ip_addr = match.group(1)
                prefix = match.group(2)
                network = ipaddress.IPv4Network(f"{ip_addr}/{prefix}", strict=False)
                result["subnet"] = str(network)

    except Exception as e:
        print(f"Network detection error: {e}")

    return result


def find_free_ips(subnet_str, gateway, count=3, start_offset=200):
    """Find consecutive free IPs in subnet by pinging."""
    free_ips = []
    try:
        network = ipaddress.IPv4Network(subnet_str, strict=False)
        hosts = list(network.hosts())

        start_index = min(start_offset, len(hosts) - count - 1)

        for i in range(start_index, len(hosts)):
            ip = str(hosts[i])

            if ip == gateway:
                continue

            ping = subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                capture_output=True, timeout=3
            )

            if ping.returncode != 0:
                free_ips.append(ip)
                if len(free_ips) >= count:
                    break
            else:
                free_ips = []

    except Exception as e:
        print(f"IP scan error: {e}")

    return free_ips


@app.route("/api/network/detect", methods=["GET"])
@require_auth
def api_network_detect():
    info = detect_network_info()

    if info["subnet"] and info["gateway"]:
        info["suggested_ips"] = find_free_ips(info["subnet"], info["gateway"])

    return jsonify(info)


@app.route("/api/network/validate-ip", methods=["POST"])
@require_auth
def api_validate_ip():
    data = request.get_json()
    ip = data.get("ip", "")

    try:
        ping = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True, timeout=3
        )
        in_use = ping.returncode == 0
    except Exception:
        in_use = False

    return jsonify({"ip": ip, "in_use": in_use})


# ══════════════════════════════════════════════════════════════
#  CONFIG FILE GENERATORS
# ══════════════════════════════════════════════════════════════

def generate_docker_compose(config, host_project_path):
    """Generate docker-compose.yml with user configuration."""
    n = config["network"]
    d = config["database"]
    a = config["admin"]

    return f"""name: assetmanagement
services:
  mariadb:
    image: mariadb:10.11
    container_name: asset-mariadb
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: {d['root_password']}
      MYSQL_DATABASE: {d['name']}
      MYSQL_USER: {d['user']}
      MYSQL_PASSWORD: {d['password']}
    volumes:
      - {host_project_path}/data/db:/var/lib/mysql
    networks:
      asset-macvlan:
        ipv4_address: {n['ip_db']}
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u{d['user']}", "-p{d['password']}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: asset-redis
    restart: unless-stopped
    command: redis-server --save "" --appendonly no --maxmemory 64mb --maxmemory-policy allkeys-lru
    networks:
      asset-macvlan:
        ipv4_address: {n['ip_redis']}
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: asset-app
    restart: unless-stopped
    environment:
      DATABASE_URL: mysql+pymysql://{d['user']}:{d['password']}@{n['ip_db']}:3306/{d['name']}
      DB_HOST: {n['ip_db']}
      DB_PORT: "3306"
      DB_USER: {d['user']}
      DB_PASSWORD: {d['password']}
      DB_NAME: {d['name']}
      AUDIT_LOG_ENCRYPTION_KEY: ${{AUDIT_LOG_ENCRYPTION_KEY}}
      SKIP_MIGRATIONS: "true"
      REDIS_URL: redis://{n['ip_redis']}:6379/0
    volumes:
      - {host_project_path}/data:/app/data
    networks:
      asset-macvlan:
        ipv4_address: {n['ip_app']}
    depends_on:
      mariadb:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: >
      sh -c "chmod +x /app/entrypoint.sh && /app/entrypoint.sh"

  compliance:
    build:
      context: ./compliance
      dockerfile: Dockerfile
    container_name: asset-compliance
    environment:
      APP_URL: {n.get('protocol', 'http')}://{n['ip_app']}:{n['port']}
      ADMIN_USERNAME: {a['username']}
      ADMIN_PASSWORD: {a['password']}
    volumes:
      - {host_project_path}/data/compliance:/app/reports
    networks:
      asset-macvlan:
    profiles:
      - compliance
    depends_on:
      app:
        condition: service_started
networks:
  asset-macvlan:
    external: true
"""


def generate_env_file(config):
    """Generate backend/.env with user configuration."""
    n = config["network"]
    d = config["database"]
    protocol = n.get("protocol", "http")
    jwt_secret = secrets.token_urlsafe(64)
    audit_key_bytes = secrets.token_bytes(32)
    audit_key = base64.urlsafe_b64encode(audit_key_bytes).decode()

    return f"""# === IT ASSET MANAGER — CONFIGURAZIONE ===
# Generato dal Bootstrap Wizard: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}

# Application
APP_NAME=asset-management
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO

# Database
DB_HOST={n['ip_db']}
DB_PORT=3306
DB_NAME={d['name']}
DB_USER={d['user']}
DB_PASSWORD={d['password']}

# JWT Security
JWT_SECRET={jwt_secret}
JWT_ALGO=HS256
JWT_EXPIRE_MINUTES=480

# CORS Origins
CORS_ORIGINS={protocol}://{n['ip_app']}:{n['port']}

# Security
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_API=100/minute
PASSWORD_MIN_LENGTH=12
AUDIT_LOG_ENCRYPTION_KEY={audit_key}
# Admin credentials (used by compliance tests)
ADMIN_USERNAME={config['admin']['username']}
ADMIN_PASSWORD={config['admin']['password']}

# Compliance guide (host info for UI)
HOST_IP={n.get('host_ip', '')}
PROJECT_PATH={config.get('host_project_path', '')}
SSH_USER={config.get('ssh_user', '')}
""", audit_key


def generate_config_document(config, include_admin_password=True):
    """Generate printable configuration document."""
    n = config["network"]
    d = config["database"]
    a = config["admin"]
    protocol = n.get("protocol", "http")
    now = datetime.datetime.now().strftime("%d/%m/%Y, %H:%M")
    url = f"{protocol}://{n['ip_app']}:{n['port']}"

    admin_pwd_line = a['password'] if include_admin_password else "[non inclusa nel documento]"

    return f"""════════════════════════════════════════════════════
  IT ASSET MANAGER — CONFIGURAZIONE SISTEMA
════════════════════════════════════════════════════

Data installazione:    {now}
Versione applicazione:  IT Asset Manager v2.7.5

─── RETE ───

Interfaccia di rete:   {n['interface']}
Subnet:                {n['subnet']}
Gateway:               {n['gateway']}
IP Applicazione:       {n['ip_app']}
IP Database:           {n['ip_db']}
IP Cache (Redis):      {n['ip_redis']}
Porta Applicazione:    {n['port']}

URL di accesso:  {url}

─── DATABASE ───

Nome Database:         {d['name']}
Utente Applicativo:    {d['user']}
Password Utente Applicativo:  {d['password']}
Password Root (Amministratore):         {d['root_password']}

─── AMMINISTRATORE ───

Nome completo:         {a['firstname']} {a['lastname']}
Email:                 {a['email']}
Nome utente:           {a['username']}
Password:              {admin_pwd_line}

════════════════════════════════════════════════════
⚠️ DOCUMENTO RISERVATO — Conservare in un luogo sicuro
   Contiene credenziali di accesso al sistema
════════════════════════════════════════════════════"""


# ══════════════════════════════════════════════════════════════
#  CONFIG FILE DOWNLOAD (called from Step 5 in frontend)
# ══════════════════════════════════════════════════════════════

@app.route("/api/config-file", methods=["POST"])
@require_auth
def api_config_file():
    data = request.get_json()
    include_pwd = data.get("include_admin_password", True)
    content = generate_config_document(data, include_admin_password=include_pwd)
    return jsonify({"content": content})


# ══════════════════════════════════════════════════════════════
#  SSE HELPER
# ══════════════════════════════════════════════════════════════

def sse_event(event_type, message, progress=None, step=None, extra=None):
    """Format a Server-Sent Event."""
    data = {"type": event_type, "message": message}
    if progress is not None:
        data["progress"] = progress
    if step is not None:
        data["step"] = step
    if extra is not None:
        data.update(extra)
    return f"data: {json.dumps(data)}\n\n"


# ══════════════════════════════════════════════════════════════
#  SEED DATA — 30 asset_types from production
# ══════════════════════════════════════════════════════════════

SEED_ASSET_TYPES_SQL = """SET FOREIGN_KEY_CHECKS=0;
INSERT INTO asset_types (id, name, parent_id, is_active) VALUES
(1, 'Hardware', NULL, 1),
(2, 'Computer', 1, 1),
(3, 'PC Desktop', 2, 1),
(4, 'Laptop', 2, 1),
(5, 'Workstation', 2, 1),
(6, 'Tablet', 2, 1),
(7, 'Monitor', 1, 1),
(8, 'Monitor Standard', 7, 1),
(9, 'Monitor Professionale', 7, 1),
(10, 'Periferiche Input/Output', 1, 1),
(11, 'Tastiera', 10, 1),
(12, 'Mouse', 10, 1),
(13, 'Webcam', 10, 1),
(14, 'Periferiche Rete', 1, 1),
(15, 'Docking Station', 14, 1),
(16, 'Hub USB', 14, 1),
(17, 'Switch di rete', 14, 1),
(18, 'Telefonia', 1, 1),
(19, 'Telefono VoIP', 18, 1),
(20, 'Smartphone Aziendale', 18, 1),
(21, 'Stampanti', 1, 1),
(22, 'Stampante Laser', 21, 1),
(23, 'Stampante Inkjet', 21, 1),
(24, 'Multifunzione', 21, 1),
(25, 'Server/Networking', 1, 1),
(26, 'Server', 25, 1),
(27, 'NAS', 25, 1),
(28, 'Router/Switch Manageable', 25, 1),
(29, 'Cuffie', 10, 1),
(30, 'Lettore Barcode', 10, 1);
SET FOREIGN_KEY_CHECKS=1;"""


# ══════════════════════════════════════════════════════════════
#  INSTALL ROUTE — 16 step sequence
# ══════════════════════════════════════════════════════════════

EXPECTED_TABLES = sorted([
    "alembic_version", "asset_types", "assets", "assignment_items",
    "assignments", "audit_logs", "badges", "document_templates",
    "documents", "inventory_skus", "location_types", "locations",
    "people", "sims", "sites", "suppliers", "users"
])


# ═══════════════════════════════════════════════════════════
# INSTALLAZIONE A STEP SINGOLI — 22 step con checkpoint
# ═══════════════════════════════════════════════════════════

@app.route("/api/install/init", methods=["POST"])
@require_auth
def api_install_init():
    """Receive form data and initialize install state."""
    global install_state
    host_path = detect_host_project_path()
    install_state = {
        "current_step": 0,
        "data": request.get_json(),
        "completed": [],
        "debug_log": [],
        "host_project_path": host_path
    }
    debug_log(f"Install initialized with form data (host_path={host_path})")
    return jsonify({"status": "ok", "message": "Installazione inizializzata", "next_step": 1})


@app.route("/api/install/debug", methods=["GET"])
@require_auth
def api_install_debug():
    """Return current install state for debugging."""
    return jsonify({
        "current_step": install_state["current_step"],
        "completed": install_state["completed"],
        "debug_log": install_state["debug_log"][-50:],
        "has_data": install_state["data"] is not None
    })


@app.route("/api/install/step/<int:step_num>", methods=["POST"])
@require_auth
def api_install_step(step_num):
    """Execute a single install step with checkpoint verification."""
    global install_state, last_config_content

    if install_state["data"] is None:
        return jsonify({"status": "error", "message": "Installazione non inizializzata. Chiama /api/install/init prima."}), 400

    if step_num != install_state["current_step"] + 1:
        return jsonify({"status": "error", "message": f"Step {step_num} fuori sequenza. Step atteso: {install_state['current_step'] + 1}"}), 400

    data = install_state["data"]
    n = data["network"]
    d = data["database"]
    a = data["admin"]
    protocol = data.get("protocol", "http")

    debug_log(f"=== STEP {step_num} START ===")

    try:
        # ─── STEP 1: Genera docker-compose.yml + backend/.env ───
        if step_num == 1:
            debug_log("Generating backend/.env")
            # Enrich config with host info for compliance guide
            data["host_project_path"] = install_state["host_project_path"]
            # Extract SSH user from host project path (e.g. /home/mattia/AssetManagement -> mattia)
            _path_parts = install_state["host_project_path"].split("/")
            data["ssh_user"] = _path_parts[2] if len(_path_parts) >= 3 and _path_parts[1] == "home" else ""
            # Detect host IP (wizard runs with network_mode: host)
            try:
                _host_ip_result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
                data["network"]["host_ip"] = _host_ip_result.stdout.strip().split()[0] if _host_ip_result.stdout.strip() else ""
            except Exception:
                data["network"]["host_ip"] = ""
            env_content, audit_key = generate_env_file(data)
            env_path = os.path.join(PROJECT_ROOT, "backend", ".env")
            with open(env_path, "w") as f:
                f.write(env_content)
            debug_log(f".env written to {env_path}")

            debug_log("Generating docker-compose.yml")
            compose_content = generate_docker_compose(data, install_state["host_project_path"])
            compose_content = compose_content.replace("${AUDIT_LOG_ENCRYPTION_KEY}", audit_key)
            compose_path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
            with open(compose_path, "w") as f:
                f.write(compose_content)
            debug_log(f"docker-compose.yml written to {compose_path}")

            # Checkpoint
            if not os.path.isfile(env_path):
                return jsonify({"status": "error", "message": "Checkpoint fallito: backend/.env non trovato"})
            if not os.path.isfile(compose_path):
                return jsonify({"status": "error", "message": "Checkpoint fallito: docker-compose.yml non trovato"})

            debug_log("CHECKPOINT OK: both config files exist")
            result = {"status": "ok", "message": "File di configurazione creati e verificati",
                      "details": {"files": ["docker-compose.yml", "backend/.env"]}}

        # ─── STEP 2: Crea rete macvlan ───
        elif step_num == 2:
            debug_log(f"Creating macvlan network: subnet={n['subnet']} gw={n['gateway']} parent={n['interface']}")
            create_net = subprocess.run(
                ["docker", "network", "create", "-d", "macvlan",
                 "--subnet", n["subnet"], "--gateway", n["gateway"],
                 "-o", f"parent={n['interface']}", "asset-macvlan"],
                capture_output=True, text=True, timeout=15
            )
            if create_net.returncode != 0:
                if "already exists" in create_net.stderr:
                    debug_log("Network already exists, continuing")
                else:
                    debug_log(f"Network creation FAILED: {create_net.stderr.strip()}")
                    return jsonify({"status": "error", "message": f"Errore creazione rete: {create_net.stderr.strip()}"})

            # Checkpoint
            verify_net = subprocess.run(
                ["docker", "network", "inspect", "asset-macvlan"],
                capture_output=True, text=True, timeout=10
            )
            if verify_net.returncode != 0:
                return jsonify({"status": "error", "message": "Checkpoint fallito: rete macvlan non trovata"})

            debug_log("CHECKPOINT OK: macvlan network verified")
            result = {"status": "ok", "message": "Rete macvlan creata e verificata"}

        # ─── STEP 3: Pull immagini MariaDB + Redis ───
        elif step_num == 3:
            debug_log("Pulling mariadb:10.11")
            pull_db = subprocess.run(
                ["docker", "pull", "mariadb:10.11"],
                capture_output=True, text=True, timeout=300
            )
            if pull_db.returncode != 0:
                debug_log(f"MariaDB pull FAILED: {pull_db.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore download MariaDB: {pull_db.stderr.strip()}"})
            debug_log("MariaDB pulled OK")

            debug_log("Pulling redis:7-alpine")
            pull_redis = subprocess.run(
                ["docker", "pull", "redis:7-alpine"],
                capture_output=True, text=True, timeout=300
            )
            if pull_redis.returncode != 0:
                debug_log(f"Redis pull FAILED: {pull_redis.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore download Redis: {pull_redis.stderr.strip()}"})
            debug_log("Redis pulled OK")

            # Checkpoint
            check_db = subprocess.run(["docker", "image", "inspect", "mariadb:10.11"], capture_output=True, text=True, timeout=10)
            check_redis = subprocess.run(["docker", "image", "inspect", "redis:7-alpine"], capture_output=True, text=True, timeout=10)
            if check_db.returncode != 0 or check_redis.returncode != 0:
                return jsonify({"status": "error", "message": "Checkpoint fallito: immagini non trovate"})

            debug_log("CHECKPOINT OK: both images verified")
            result = {"status": "ok", "message": "Immagini MariaDB e Redis scaricate e verificate"}

        # ─── STEP 4: Pulizia data/db + Avvio MariaDB + health check ───
        elif step_num == 4:
            db_data_path = os.path.join(PROJECT_ROOT, "data", "db")

            if os.path.exists(db_data_path):
                debug_log(f"Cleaning {db_data_path}")
                clean = subprocess.run(
                    ["docker", "run", "--rm", "-v", f"{db_data_path}:/data", "alpine", "sh", "-c",
                     "find /data -mindepth 1 -delete 2>/dev/null; ls -la /data/ 2>/dev/null || true"],
                    capture_output=True, text=True, timeout=60
                )
                debug_log(f"Clean output: {clean.stdout.strip()[:200]}")
                if clean.returncode != 0:
                    stderr_clean = clean.stderr.strip()
                    if "No such file" not in stderr_clean:
                        debug_log(f"Clean FAILED: {stderr_clean}")
                        return jsonify({"status": "error", "message": f"Errore pulizia data/db: {stderr_clean}"})
                debug_log("data/db cleaned")

            os.makedirs(db_data_path, exist_ok=True)

            debug_log("Starting MariaDB")
            start_db = subprocess.run(
                ["docker", "compose", "-f", os.path.join(PROJECT_ROOT, "docker-compose.yml"), "up", "-d", "mariadb"],
                capture_output=True, text=True, timeout=60, cwd=PROJECT_ROOT
            )
            if start_db.returncode != 0:
                debug_log(f"MariaDB start FAILED: {start_db.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore avvio MariaDB: {start_db.stderr.strip()}"})

            debug_log("Waiting for MariaDB healthy...")
            db_healthy = False
            for i in range(30):
                check = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Health.Status}}", "asset-mariadb"],
                    capture_output=True, text=True, timeout=10
                )
                status = check.stdout.strip()
                debug_log(f"MariaDB health check attempt {i+1}/30: {status}")
                if status == "healthy":
                    db_healthy = True
                    break
                time.sleep(5)

            if not db_healthy:
                return jsonify({"status": "error", "message": "MariaDB non risponde dopo 150 secondi"})

            debug_log("CHECKPOINT OK: MariaDB healthy")
            result = {"status": "ok", "message": "MariaDB avviato e healthy"}

        # ─── STEP 5: Setup DB — Forza password + Crea database + Crea utente ───
        elif step_num == 5:
            time.sleep(3)

            # 5a. Forza password root
            debug_log("Forcing root password")
            root_pw_sql = f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{d['root_password']}'; ALTER USER 'root'@'%' IDENTIFIED BY '{d['root_password']}'; FLUSH PRIVILEGES;"
            pw_result = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", "-e", root_pw_sql],
                capture_output=True, text=True, timeout=15
            )
            if pw_result.returncode != 0:
                debug_log(f"Root password FAILED: {pw_result.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore password root: {pw_result.stderr.strip()}"})
            debug_log("Root password set OK")

            # 5b. Crea database se non esiste
            debug_log(f"Creating database {d['name']} if not exists")
            create_db_sql = f"CREATE DATABASE IF NOT EXISTS `{d['name']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            db_result = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", "-e", create_db_sql],
                capture_output=True, text=True, timeout=15
            )
            if db_result.returncode != 0:
                debug_log(f"Create DB FAILED: {db_result.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore creazione database: {db_result.stderr.strip()}"})
            debug_log(f"Database {d['name']} exists")

            # 5c. Crea utente app
            debug_log(f"Creating user {d['user']}")
            create_user_sql = (
                f"CREATE USER IF NOT EXISTS '{d['user']}'@'%' IDENTIFIED BY '{d['password']}';"
                f"ALTER USER '{d['user']}'@'%' IDENTIFIED BY '{d['password']}';"
                f"GRANT ALL PRIVILEGES ON `{d['name']}`.* TO '{d['user']}'@'%';"
                f"FLUSH PRIVILEGES;"
            )
            user_result = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", "-e", create_user_sql],
                capture_output=True, text=True, timeout=15
            )
            if user_result.returncode != 0:
                debug_log(f"Create user FAILED: {user_result.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore creazione utente: {user_result.stderr.strip()}"})
            debug_log(f"User {d['user']} created")

            # Checkpoint: DB vuoto con nuova password
            verify_empty = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", "SHOW TABLES"],
                capture_output=True, text=True, timeout=15
            )
            if verify_empty.returncode != 0:
                debug_log(f"Verify FAILED: {verify_empty.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Checkpoint fallito: {verify_empty.stderr.strip()}"})
            tables_found = [t.strip() for t in verify_empty.stdout.strip().split('\n') if t.strip()]
            if len(tables_found) > 0:
                return jsonify({"status": "error", "message": f"DB non vuoto: trovate {len(tables_found)} tabelle"})

            debug_log("CHECKPOINT OK: DB empty and accessible")
            result = {"status": "ok", "message": "Database configurato, vuoto e accessibile",
                      "details": {"db": d["name"], "user": d["user"]}}

        # ─── STEP 6: Build app ───
        elif step_num == 6:
            debug_log("Building app image")
            build_app = subprocess.run(
                ["docker", "compose", "-f", os.path.join(PROJECT_ROOT, "docker-compose.yml"), "build", "app"],
                capture_output=True, text=True, timeout=600, cwd=PROJECT_ROOT
            )
            if build_app.returncode != 0:
                debug_log(f"Build FAILED: {build_app.stderr.strip()[-500:]}")
                return jsonify({"status": "error", "message": f"Errore build: {build_app.stderr.strip()[-500:]}"})

            # Checkpoint
            check_img = subprocess.run(
                ["docker", "image", "inspect", "assetmanagement-app:latest"],
                capture_output=True, text=True, timeout=10
            )
            if check_img.returncode != 0:
                return jsonify({"status": "error", "message": "Checkpoint fallito: immagine app non trovata"})

            debug_log("CHECKPOINT OK: app image built (assetmanagement-app:latest)")
            result = {"status": "ok", "message": "Immagine applicazione buildata e verificata"}

        # ─── STEP 7: SSL (se HTTPS, altrimenti skip) ───
        elif step_num == 7:
            if protocol == "https":
                debug_log("Generating SSL certificate")
                ssl_dir = os.path.join(PROJECT_ROOT, "data", "ssl")
                os.makedirs(ssl_dir, exist_ok=True)
                ssl_result = subprocess.run(
                    ["openssl", "req", "-x509", "-newkey", "rsa:4096", "-keyout",
                     os.path.join(ssl_dir, "key.pem"), "-out", os.path.join(ssl_dir, "cert.pem"),
                     "-days", "365", "-nodes", "-subj", f"/CN={n['ip_app']}"],
                    capture_output=True, text=True, timeout=30
                )
                if ssl_result.returncode != 0:
                    debug_log(f"SSL FAILED: {ssl_result.stderr.strip()}")
                    return jsonify({"status": "error", "message": f"Errore SSL: {ssl_result.stderr.strip()}"})
                debug_log("CHECKPOINT OK: SSL certificate generated")
                result = {"status": "ok", "message": "Certificato SSL generato"}
            else:
                debug_log("HTTP selected, skipping SSL")
                result = {"status": "ok", "message": "Protocollo HTTP, SSL non richiesto (skip)"}

        # ─── STEP 8: Tabelle Livello 0 (no FK esterne) ───
        elif step_num == 8:
            debug_log("Creating Level 0 tables: sites, suppliers, location_types, asset_types, document_templates")
            success, created, err = create_ddl_tables(LEVEL_0_TABLES, d["name"], d["root_password"])
            if not success:
                debug_log(err)
                return jsonify({"status": "error", "message": err})

            # Checkpoint: count tables
            check = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()"],
                capture_output=True, text=True, timeout=10
            )
            count = check.stdout.strip()
            debug_log(f"Table count after Level 0: {count}")
            if count != "5":
                return jsonify({"status": "error", "message": f"Checkpoint fallito: attese 5 tabelle, trovate {count}"})

            debug_log("CHECKPOINT OK: Level 0 tables created")
            result = {"status": "ok", "message": f"5 tabelle Livello 0 create: {', '.join(created)}"}

        # ─── STEP 9: Tabelle Livello 1 (dipendono da L0) ───
        elif step_num == 9:
            debug_log("Creating Level 1 tables: people, locations, inventory_skus")
            success, created, err = create_ddl_tables(LEVEL_1_TABLES, d["name"], d["root_password"])
            if not success:
                debug_log(err)
                return jsonify({"status": "error", "message": err})

            # Checkpoint
            check = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()"],
                capture_output=True, text=True, timeout=10
            )
            count = check.stdout.strip()
            debug_log(f"Table count after Level 1: {count}")
            if count != "8":
                return jsonify({"status": "error", "message": f"Checkpoint fallito: attese 8 tabelle, trovate {count}"})

            debug_log("CHECKPOINT OK: Level 1 tables created")
            result = {"status": "ok", "message": f"3 tabelle Livello 1 create: {', '.join(created)}"}

        # ─── STEP 10: Tabelle Livello 2 (dipendono da L1) ───
        elif step_num == 10:
            debug_log("Creating Level 2 tables: users, assets, sims, badges, assignments")
            success, created, err = create_ddl_tables(LEVEL_2_TABLES, d["name"], d["root_password"])
            if not success:
                debug_log(err)
                return jsonify({"status": "error", "message": err})

            # Checkpoint
            check = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()"],
                capture_output=True, text=True, timeout=10
            )
            count = check.stdout.strip()
            debug_log(f"Table count after Level 2: {count}")
            if count != "13":
                return jsonify({"status": "error", "message": f"Checkpoint fallito: attese 13 tabelle, trovate {count}"})

            debug_log("CHECKPOINT OK: Level 2 tables created")
            result = {"status": "ok", "message": f"5 tabelle Livello 2 create: {', '.join(created)}"}

        # ─── STEP 11: Tabelle Livello 3 (dipendono da L2) ───
        elif step_num == 11:
            debug_log("Creating Level 3 tables: assignment_items, audit_logs, documents")
            success, created, err = create_ddl_tables(LEVEL_3_TABLES, d["name"], d["root_password"])
            if not success:
                debug_log(err)
                return jsonify({"status": "error", "message": err})

            # Checkpoint
            check = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()"],
                capture_output=True, text=True, timeout=10
            )
            count = check.stdout.strip()
            debug_log(f"Table count after Level 3: {count}")
            if count != "16":
                return jsonify({"status": "error", "message": f"Checkpoint fallito: attese 16 tabelle, trovate {count}"})

            debug_log("CHECKPOINT OK: Level 3 tables created")
            result = {"status": "ok", "message": f"3 tabelle Livello 3 create: {', '.join(created)}"}

        # ─── STEP 12: Crea tabella alembic_version ───
        elif step_num == 12:
            # Drop if exists (clears orphaned tablespace)
            subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-e",
                 "DROP TABLE IF EXISTS `alembic_version`;"],
                capture_output=True, text=True, timeout=15
            )
            debug_log("Creating alembic_version table")
            av_result = subprocess.run(
                ["docker", "exec", "-i", "-e", f"MYSQL_PWD={d['root_password']}",
                 "asset-mariadb", "mysql", "-uroot", d["name"]],
                input=ALEMBIC_VERSION_TABLE,
                capture_output=True, text=True, timeout=15
            )
            if av_result.returncode != 0:
                debug_log(f"alembic_version CREATE FAILED: {av_result.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore creazione alembic_version: {av_result.stderr.strip()}"})

            # Checkpoint: 17 tables total
            check = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE()"],
                capture_output=True, text=True, timeout=10
            )
            count = check.stdout.strip()
            debug_log(f"Table count after alembic_version: {count}")
            if count != "17":
                return jsonify({"status": "error", "message": f"Checkpoint fallito: attese 17 tabelle, trovate {count}"})

            debug_log("CHECKPOINT OK: alembic_version table created (17 total)")
            result = {"status": "ok", "message": "Tabella alembic_version creata (17 tabelle totali)"}

        # ─── STEP 13: Scrittura head in alembic_version ───
        elif step_num == 13:
            debug_log(f"Writing Alembic head: {ALEMBIC_HEAD}")
            insert_sql = f"INSERT INTO alembic_version (version_num) VALUES ('{ALEMBIC_HEAD}');"
            ins_result = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-e", insert_sql],
                capture_output=True, text=True, timeout=10
            )
            if ins_result.returncode != 0:
                debug_log(f"INSERT alembic head FAILED: {ins_result.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore scrittura alembic head: {ins_result.stderr.strip()}"})

            # Checkpoint: verify head value
            verify = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", "SELECT version_num FROM alembic_version"],
                capture_output=True, text=True, timeout=10
            )
            head = verify.stdout.strip()
            debug_log(f"alembic_version head: {head}")
            if head != ALEMBIC_HEAD:
                return jsonify({"status": "error", "message": f"Checkpoint fallito: head={head}, atteso={ALEMBIC_HEAD}"})

            debug_log(f"CHECKPOINT OK: alembic head = {ALEMBIC_HEAD}")
            result = {"status": "ok", "message": f"Alembic head impostato: {ALEMBIC_HEAD}"}

        # ─── STEP 14: Avvio app ───
        elif step_num == 14:
            debug_log("Starting app container")
            start_app = subprocess.run(
                ["docker", "compose", "-f", os.path.join(PROJECT_ROOT, "docker-compose.yml"), "up", "-d", "app"],
                capture_output=True, text=True, timeout=60, cwd=PROJECT_ROOT
            )
            if start_app.returncode != 0:
                debug_log(f"App start FAILED: {start_app.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore avvio app: {start_app.stderr.strip()}"})

            debug_log("Waiting for app to stabilize...")
            app_running = False
            for i in range(24):
                time.sleep(5)
                check_app = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Status}}:{{.RestartCount}}", "asset-app"],
                    capture_output=True, text=True, timeout=10
                )
                output = check_app.stdout.strip()
                debug_log(f"App status check {i+1}/24: {output}")
                if output.startswith("running:"):
                    restart_count = int(output.split(":")[1])
                    if restart_count == 0:
                        app_running = True
                        break
                    elif restart_count > 2:
                        logs = subprocess.run(["docker", "logs", "--tail", "30", "asset-app"], capture_output=True, text=True, timeout=10)
                        debug_log(f"App crash loop! Logs: {logs.stderr.strip()[-300:]}")
                        return jsonify({"status": "error", "message": f"App in crash loop (restart: {restart_count})",
                                        "details": {"logs": logs.stderr.strip()[-500:]}})

            if not app_running:
                logs = subprocess.run(["docker", "logs", "--tail", "30", "asset-app"], capture_output=True, text=True, timeout=10)
                return jsonify({"status": "error", "message": "App non si avvia dopo 120 secondi",
                                "details": {"logs": logs.stderr.strip()[-500:]}})

            debug_log("CHECKPOINT OK: app running, no restarts")
            result = {"status": "ok", "message": "Applicazione avviata (SKIP_MIGRATIONS=true)"}

        # ─── STEP 15: Verifica schema ───
        elif step_num == 15:
            debug_log("Verifying schema")
            found_tables = []
            for attempt in range(6):
                schema_result = subprocess.run(
                    ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", "SHOW TABLES"],
                    capture_output=True, text=True, timeout=15
                )
                if schema_result.returncode != 0:
                    debug_log(f"Schema check attempt {attempt+1} FAILED: {schema_result.stderr.strip()}")
                    if attempt < 5:
                        time.sleep(5)
                        continue
                    return jsonify({"status": "error", "message": f"Errore verifica schema: {schema_result.stderr.strip()}"})

                found_tables = sorted([t.strip() for t in schema_result.stdout.strip().split('\n') if t.strip()])
                debug_log(f"Schema check attempt {attempt+1}: found {len(found_tables)} tables")
                if len(found_tables) >= len(EXPECTED_TABLES):
                    break
                if attempt < 5:
                    time.sleep(5)

            if found_tables != EXPECTED_TABLES:
                missing = sorted(set(EXPECTED_TABLES) - set(found_tables))
                extra = sorted(set(found_tables) - set(EXPECTED_TABLES))
                debug_log(f"Schema MISMATCH: found={found_tables} missing={missing} extra={extra}")
                return jsonify({"status": "error", "message": f"Schema non valido. Trovate {len(found_tables)}, attese {len(EXPECTED_TABLES)}.",
                                "details": {"missing": missing, "extra": extra, "found": found_tables}})

            debug_log(f"CHECKPOINT OK: {len(found_tables)} tables match")
            result = {"status": "ok", "message": f"Schema verificato: {len(found_tables)} tabelle",
                      "details": {"tables": found_tables}}

        # ─── STEP 16: Seed asset_types ───
        elif step_num == 16:
            debug_log("Seeding asset_types")
            seed_result = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-e", SEED_ASSET_TYPES_SQL],
                capture_output=True, text=True, timeout=15
            )
            if seed_result.returncode != 0:
                debug_log(f"Seed FAILED: {seed_result.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore seed asset_types: {seed_result.stderr.strip()}"})

            # Checkpoint
            count_result = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", "SELECT COUNT(*) FROM asset_types"],
                capture_output=True, text=True, timeout=10
            )
            count = count_result.stdout.strip()
            debug_log(f"asset_types count: {count}")
            if count != "30":
                return jsonify({"status": "error", "message": f"Checkpoint fallito: asset_types count={count}, atteso 30"})

            # Seed document_templates (default empty template for letterhead upload)
            debug_log("Seeding document_templates")
            seed_template_sql = (
                "INSERT INTO document_templates (name, description, is_default, is_active, created_at, updated_at) "
                "VALUES ('Template Predefinito', 'Template base per documenti di assegnazione', 1, 1, NOW(), NOW());"
            )
            template_result = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-e", seed_template_sql],
                capture_output=True, text=True, timeout=15
            )
            if template_result.returncode != 0:
                debug_log(f"Seed template FAILED: {template_result.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore seed document_templates: {template_result.stderr.strip()}"})

            # Checkpoint template
            tpl_count = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", "SELECT COUNT(*) FROM document_templates WHERE is_default=1"],
                capture_output=True, text=True, timeout=10
            )
            debug_log(f"document_templates default count: {tpl_count.stdout.strip()}")
            if tpl_count.stdout.strip() != "1":
                return jsonify({"status": "error", "message": "Checkpoint fallito: template predefinito non trovato"})

            debug_log("CHECKPOINT OK: default document template created")

            debug_log("CHECKPOINT OK: 30 asset_types + default template")
            result = {"status": "ok", "message": "30 categorie asset e template predefinito inseriti e verificati"}

        # ─── STEP 17: Creazione Admin ───
        elif step_num == 17:
            # 11a. Crea persona
            debug_log(f"Creating person: {a['firstname']} {a['lastname']}")
            admin_person_sql = (
                f"INSERT INTO people (first_name, last_name, email, is_active, created_at, updated_at) "
                f"VALUES ('{a['firstname']}', '{a['lastname']}', '{a['email']}', 1, NOW(), NOW());"
            )
            person_result = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-e", admin_person_sql],
                capture_output=True, text=True, timeout=15
            )
            if person_result.returncode != 0:
                debug_log(f"Person create FAILED: {person_result.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore creazione persona: {person_result.stderr.strip()}"})

            # 11b. Ottieni person_id
            get_pid = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", f"SELECT id FROM people WHERE email='{a['email']}' LIMIT 1"],
                capture_output=True, text=True, timeout=10
            )
            person_id = get_pid.stdout.strip()
            debug_log(f"person_id: {person_id}")
            if not person_id:
                return jsonify({"status": "error", "message": "Impossibile recuperare person_id"})

            # 11c. Hash password via app container
            debug_log("Hashing admin password via app container")
            hash_result = subprocess.run(
                ["docker", "exec", "asset-app", "python", "-c",
                 f"from app.core.security import hash_password; print(hash_password('{a['password']}'))"],
                capture_output=True, text=True, timeout=15
            )
            if hash_result.returncode != 0:
                debug_log(f"Hash FAILED: {hash_result.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore hash password: {hash_result.stderr.strip()}"})
            password_hash = hash_result.stdout.strip()
            debug_log(f"Password hashed OK (len={len(password_hash)})")

            # 11d. Crea utente
            debug_log(f"Creating user: {a['username']}")
            admin_user_sql = (
                f"INSERT INTO users (username, password_hash, role, is_active, person_id, created_at) "
                f"VALUES ('{a['username']}', '{password_hash}', 'admin', 1, {person_id}, NOW());"
            )
            user_result = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-e", admin_user_sql],
                capture_output=True, text=True, timeout=15
            )
            if user_result.returncode != 0:
                debug_log(f"User create FAILED: {user_result.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore creazione utente: {user_result.stderr.strip()}"})

            # Checkpoint
            verify_admin = subprocess.run(
                ["docker", "exec", "-e", f"MYSQL_PWD={d['root_password']}", "asset-mariadb", "mysql", "-uroot", d["name"], "-N", "-e", f"SELECT COUNT(*) FROM users WHERE username='{a['username']}'"],
                capture_output=True, text=True, timeout=10
            )
            debug_log(f"Admin verify: {verify_admin.stdout.strip()}")
            if verify_admin.stdout.strip() != "1":
                return jsonify({"status": "error", "message": "Checkpoint fallito: utente Admin non trovato"})

            debug_log("CHECKPOINT OK: admin created")
            result = {"status": "ok", "message": f"Account Admin '{a['username']}' creato e verificato"}

        # ─── STEP 18: Avvio Redis ───
        elif step_num == 18:
            debug_log("Starting Redis")
            start_redis = subprocess.run(
                ["docker", "compose", "-f", os.path.join(PROJECT_ROOT, "docker-compose.yml"), "up", "-d", "redis"],
                capture_output=True, text=True, timeout=60, cwd=PROJECT_ROOT
            )
            if start_redis.returncode != 0:
                debug_log(f"Redis start FAILED: {start_redis.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore avvio Redis: {start_redis.stderr.strip()}"})

            redis_healthy = False
            for i in range(12):
                check_r = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Health.Status}}", "asset-redis"],
                    capture_output=True, text=True, timeout=10
                )
                status = check_r.stdout.strip()
                debug_log(f"Redis health check {i+1}/12: {status}")
                if status == "healthy":
                    redis_healthy = True
                    break
                time.sleep(5)

            if not redis_healthy:
                return jsonify({"status": "error", "message": "Redis non risponde dopo 60 secondi"})

            debug_log("CHECKPOINT OK: Redis healthy")
            result = {"status": "ok", "message": "Redis avviato e healthy"}

        # ─── STEP 19: Copia frontend ───
        elif step_num == 19:
            dist_path = os.path.join(PROJECT_ROOT, "frontend", "dist")
            debug_log(f"Copying frontend from {dist_path}")
            if not os.path.isdir(dist_path):
                return jsonify({"status": "error", "message": f"Cartella frontend/dist non trovata: {dist_path}"})

            copy_fe = subprocess.run(
                ["docker", "cp", f"{dist_path}/.", "asset-app:/app/static/dist/"],
                capture_output=True, text=True, timeout=30
            )
            if copy_fe.returncode != 0:
                debug_log(f"Copy FAILED: {copy_fe.stderr.strip()}")
                return jsonify({"status": "error", "message": f"Errore copia frontend: {copy_fe.stderr.strip()}"})

            # Checkpoint
            verify_idx = subprocess.run(
                ["docker", "exec", "asset-app", "test", "-f", "/app/static/dist/index.html"],
                capture_output=True, text=True, timeout=10
            )
            if verify_idx.returncode != 0:
                return jsonify({"status": "error", "message": "Checkpoint fallito: index.html non trovato nel container"})

            debug_log("CHECKPOINT OK: frontend copied")
            result = {"status": "ok", "message": "Frontend copiato e verificato"}

        # ─── STEP 20: Health check finale ───
        elif step_num == 20:
            health_url = f"{protocol}://{n['ip_app']}:{n['port']}/api/health"
            debug_log(f"Health check via docker exec (host cannot reach macvlan directly)")
            health_ok = False
            for attempt in range(6):
                hc = subprocess.run(
                    ["docker", "exec", "asset-app", "python", "-c",
                     "import urllib.request; r = urllib.request.urlopen('http://localhost:8000/api/health', timeout=10); print(r.getcode())"],
                    capture_output=True, text=True, timeout=15
                )
                debug_log(f"Health check attempt {attempt+1}: rc={hc.returncode} stdout={hc.stdout.strip()} stderr={hc.stderr.strip()[:100]}")
                if hc.returncode == 0 and hc.stdout.strip() == "200":
                    health_ok = True
                    break
                if attempt < 5:
                    time.sleep(5)

            if not health_ok:
                return jsonify({"status": "error", "message": f"Health check fallito: l'app non risponde su /api/health"})

            debug_log("CHECKPOINT OK: app reachable")
            result = {"status": "ok", "message": "Applicazione raggiungibile e funzionante",
                      "details": {"url": health_url}}

        # ─── STEP 21: File configurazione stampabile ───
        elif step_num == 21:
            url = f"{protocol}://{n['ip_app']}:{n['port']}"
            debug_log("Generating config file")
            config_text = generate_config_document(data)
            config_path = os.path.join(PROJECT_ROOT, "INSTALL_CONFIG.txt")
            with open(config_path, "w") as f:
                f.write(config_text)
            last_config_content = config_text

            if not os.path.isfile(config_path):
                return jsonify({"status": "error", "message": "Checkpoint fallito: file configurazione non creato"})

            debug_log("CHECKPOINT OK: config file written")
            result = {"status": "ok", "message": "File di configurazione generato",
                      "details": {"path": "INSTALL_CONFIG.txt"}}

        # ─── STEP 22: Completamento ───
        elif step_num == 22:
            debug_log("Writing .initialized flag")
            initialized_path = os.path.join(PROJECT_ROOT, ".initialized")
            with open(initialized_path, "w") as f:
                f.write(f"Installed: {datetime.datetime.now().isoformat()}\n")

            url = f"{protocol}://{n['ip_app']}:{n['port']}"
            debug_log("INSTALLATION COMPLETE")
            result = {"status": "ok", "message": "Installazione completata!",
                      "details": {"url": url, "username": a["username"]}}

        else:
            return jsonify({"status": "error", "message": f"Step {step_num} non esiste (1-22)"})

        # Mark step completed
        install_state["current_step"] = step_num
        install_state["completed"].append(step_num)
        debug_log(f"=== STEP {step_num} COMPLETE ===")
        return jsonify(result)

    except Exception as e:
        debug_log(f"EXCEPTION in step {step_num}: {str(e)}")
        return jsonify({"status": "error", "message": f"Errore imprevisto step {step_num}: {str(e)}"})



# ══════════════════════════════════════════════════════════════
#  CLEANUP — Shutdown wizard
# ══════════════════════════════════════════════════════════════

@app.route("/api/cleanup", methods=["POST"])
@require_auth
def api_cleanup():
    """Shutdown the wizard container."""
    def delayed_shutdown():
        time.sleep(2)
        os._exit(0)

    threading.Thread(target=delayed_shutdown, daemon=True).start()
    return jsonify({"status": "ok", "message": "Wizard in fase di spegnimento"})


# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
