# Installation Guide — IT Asset Manager v2.7.5

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Wizard Setup — Step by Step](#wizard-setup--step-by-step)
- [Post-Installation](#post-installation)
- [Compliance Testing](#compliance-testing)
- [Troubleshooting](#troubleshooting)
- [Uninstall](#uninstall)

---

## Prerequisites

Before installing IT Asset Manager, make sure your server meets these requirements.

### Hardware

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB |
| Disk | 10 GB free | 20 GB free |
| Network | Ethernet (wired) | Gigabit Ethernet |

### Software

| Requirement | Minimum Version | Check Command |
|-------------|----------------|---------------|
| Linux OS | Ubuntu 22.04+ / Debian 12+ | `cat /etc/os-release` |
| Docker Engine | 24.0+ | `docker --version` |
| Docker Compose | v2.20+ (plugin) | `docker compose version` |
| Git | 2.30+ | `git --version` |

### Network

- The server must have a **wired Ethernet connection** to the local network
- **3 free IP addresses** in the same subnet are required (for the application, database, and cache services)
- **Internet access** is required during installation to download Docker images (~600 MB total)
- The user running the installation must belong to the `docker` group

### Verify Docker permissions

```bash
# Check if your user is in the docker group
groups $(whoami) | grep -q docker && echo "OK" || echo "Add user to docker group: sudo usermod -aG docker $USER"
```

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://gitlab.com/mattia-bassi/it-asset-manager.git
cd it-asset-manager

# 2. Build and start the setup wizard
docker compose -f docker-compose.setup.yml build --no-cache
docker compose -f docker-compose.setup.yml up

# 3. Open your browser
#    → http://<server-ip>:8080

# 4. Follow the guided setup (see next section for details)
#    Wizard credentials: setup / Setup@FirstRun!
```

> **Note:** The wizard runs on port 8080 with `network_mode: host`, so it is accessible at your server's IP address on port 8080.

---

## Wizard Setup — Step by Step

### Step 0 — Language Selection

Choose your preferred language: **Italiano** or **English**. All wizard screens, validation messages, and the generated configuration document will use the selected language.

### Step 1 — Login

Enter the setup credentials:

| Field | Value |
|-------|-------|
| Username | `setup` |
| Password | `Setup@FirstRun!` |

These credentials are used **only** for the initial wizard setup and are not stored anywhere after installation.

### Step 2 — Network Configuration

The wizard will auto-detect your network settings (interface, subnet, gateway). You can choose between **Automatic** and **Manual** mode.

Configure the following:

| Setting | Description | Example |
|---------|-------------|---------|
| Network Interface | Ethernet adapter connected to your LAN | `eno1`, `eth0` |
| Subnet | Your local network in CIDR notation | `10.20.0.0/24` |
| Gateway | Your network router/gateway IP | `10.20.0.1` |
| Application IP | IP address for the web application | `10.20.0.210` |
| Database IP | IP address for MariaDB (internal only) | `10.20.0.211` |
| Cache IP | IP address for Redis (internal only) | `10.20.0.212` |
| Application Port | Port for web access | `8000` |
| Protocol | HTTP or HTTPS | `HTTP` for testing, `HTTPS` for production |

> **Important:** All 3 IP addresses must be **unused** in your network. The wizard will verify each IP via ping before proceeding.

### Step 3 — Database Credentials

Configure the MariaDB database:

| Setting | Description | Default |
|---------|-------------|---------|
| Database Name | Name of the application database | `assetdb` |
| Application User | Database user for the application | `assetapp` |
| Application Password | Password for the application user | *(choose a strong password)* |
| Root Password | MariaDB root password | *(choose a strong password)* |

> **Tip:** Use passwords of at least 12 characters with uppercase, lowercase, numbers, and special characters.

### Step 4 — Admin Account

Create the first administrator account:

| Setting | Description |
|---------|-------------|
| First Name | Administrator's first name |
| Last Name | Administrator's last name |
| Email | Administrator's email address |
| Username | Login username (min. 4 characters) |
| Password | Login password (min. 12 characters) |

This account will have full **Admin** privileges in the application.

### Step 5 — Summary & Confirmation

Review all your settings. You can:

- **Download** a configuration summary document for your records
- **Go back** to any previous step to make changes
- **Confirm** to start the installation

> **Recommendation:** Download the configuration document before proceeding. It contains all passwords and settings you will need.

### Step 6 — Automated Installation

The wizard will execute 22 installation steps automatically:

1. Generate configuration files (`docker-compose.yml` + `backend/.env`)
2. Create the macvlan Docker network
3. Download Docker images (MariaDB, Redis)
4. Start and initialize the database
5. Build the application container
6. Generate SSL certificates (if HTTPS selected)
7. Create all 17 database tables
8. Configure Alembic migration tracking
9. Start the application
10. Seed initial data (30 asset types + document template)
11. Create the admin account
12. Start Redis cache
13. Deploy the frontend
14. Run health checks
15. Generate installation record

A **live progress bar** and **log console** will show real-time status. If any step fails, you can use the **Retry** button to attempt it again.

### Step 7 — Completion

Installation is complete! You will see:

- The **URL** to access your application (e.g., `http://10.20.0.210:8000`)
- Your **admin credentials** for the first login
- A link to **download** the final installation report

> **After this step:** Close the wizard tab. The wizard container can be stopped and removed — it is no longer needed.

---

## Post-Installation

### Stop the wizard

```bash
# Stop and remove the wizard container
docker compose -f docker-compose.setup.yml down
```

### Verify the application is running

```bash
# Check all containers are up
docker ps

# Expected output: 3 containers running
# asset-app       (application)
# asset-mariadb   (database)
# asset-redis     (cache)
```

### Access the application

Open your browser and navigate to the URL shown in the wizard completion screen:

```
http://<application-ip>:<port>
```

Log in with the admin credentials you created in Step 4.

### Daily operations

```bash
# Start the application (after server reboot)
docker compose up -d

# Stop the application
docker compose down

# View application logs
docker logs --tail 50 asset-app

# Restart the application
docker restart asset-app
```

---

## Compliance Testing

IT Asset Manager includes a built-in compliance testing system that verifies **ISO 27001:2022** and **GDPR** conformity. The compliance tests run in a separate Docker container (auditor/auditee separation per ISO 27001 Clause 9.2).

### Run compliance tests

```bash
# Navigate to the project directory
cd /path/to/it-asset-manager

# Run the compliance test suite
docker compose run --rm compliance
```

The test takes approximately **90 seconds** to complete (includes rate limiting verification with a 61-second wait).

### Expected results

| Environment | Expected Score | Notes |
|-------------|---------------|-------|
| HTTP (development) | **25/26** | Only "HTTPS active connection" fails (expected) |
| HTTPS (production) | **26/26** | All 26 tests pass |

### What is tested (26 controls)

| Category | Tests | Standard |
|----------|-------|----------|
| HTTPS/TLS | 1 | ISO 27001 A.8.24 |
| Security Headers (OWASP) | 6 | ISO 27001 A.8.9 |
| Rate Limiting | 1 | ISO 27001 A.8.16 |
| Authentication | 3 | ISO 27001 A.8.5 |
| GDPR Endpoints | 5 | GDPR Art. 15-18, 20 |
| Audit Logging | 3 | ISO 27001 A.12.4.1 |
| Encryption at Rest | 3 | ISO 27001 A.8.24 |
| Log Rotation | 3 | ISO 27001 A.12.4.1 |
| Database Hardening | 1 | ISO 27001 A.8.20 |

### View results

After running the tests:

- **In the application:** Go to Settings → Compliance, click "Refresh Results"
- **On disk:** Reports are saved in `data/compliance/`
  - `latest_report.json` — JSON report (consumed by the application UI)
  - `compliance_report_YYYYMMDD_HHMMSS.pdf` — PDF report for audit documentation

---

## Troubleshooting

### Wizard does not start

```bash
# Check if port 8080 is available
ss -tlnp | grep 8080

# Check Docker socket permissions
ls -la /var/run/docker.sock

# View wizard logs
docker compose -f docker-compose.setup.yml logs
```

### Installation fails at a specific step

The wizard shows detailed logs in the console. Common issues:

| Step | Error | Solution |
|------|-------|----------|
| Pull images | `connection refused` | Check internet connectivity |
| Start MariaDB | `unhealthy` | Check if the database IP is already in use |
| Build app | `pip install failed` | Check internet connectivity |
| Create admin | `duplicate entry` | Previous installation was not cleaned up — see [Uninstall](#uninstall) |

### Application does not start after reboot

```bash
# Check container status
docker ps -a

# If containers are stopped, start them
docker compose up -d

# Check logs for errors
docker logs --tail 50 asset-app
```

### Cannot access the application from browser

```bash
# Verify the application is running
docker ps | grep asset-app

# Test from the server itself (macvlan limitation)
docker exec asset-app python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/health').read().decode())"
```

> **Note:** Due to macvlan networking, the host server cannot directly access container IPs. Use `docker exec` for local testing, or access from another device on the same network.

---

## Uninstall

To completely remove IT Asset Manager and start fresh:

```bash
# Stop all containers
docker compose down

# Remove generated files
rm -f docker-compose.yml
rm -f backend/.env
rm -f .initialized
rm -f INSTALL_CONFIG.txt

# Remove data (requires sudo — owned by Docker)
sudo rm -rf data/db
sudo rm -rf data/compliance

# Remove Docker images (optional)
docker image prune -a

# Remove Docker network
docker network rm asset-macvlan 2>/dev/null
```

After uninstalling, you can re-run the wizard to perform a fresh installation.

---

## License

IT Asset Manager is developed by **Mattia Bassi**.

---

*Document Version: 1.0 — March 2026*
