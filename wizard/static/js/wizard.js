/* ============================================
   IT ASSET MANAGER — BOOTSTRAP WIZARD
   JavaScript Engine v2.0
   Step-based installation (22 API steps)
   ============================================ */

const WizardApp = (() => {
    // --- State ---
    let currentStep = 0;
    let language = null;
    let sessionToken = null;
    let translations = {};
    let lastFailedStep = 0;
    let config = {
        network: {},
        database: {},
        admin: {},
        protocol: 'http'
    };

    // --- Constants ---
    const TOTAL_SCREENS = 8; // 0-7
    const TOTAL_INSTALL_STEPS = 22;
    const PASSWORD_MIN_LENGTH = 12;

    // Install step descriptions (used in Step 6 UI)
    const INSTALL_STEP_NAMES = {
        1: { it: 'Generazione file di configurazione', en: 'Generating configuration files' },
        2: { it: 'Creazione rete macvlan', en: 'Creating macvlan network' },
        3: { it: 'Download immagini Docker', en: 'Downloading Docker images' },
        4: { it: 'Avvio MariaDB', en: 'Starting MariaDB' },
        5: { it: 'Configurazione database', en: 'Configuring database' },
        6: { it: 'Build applicazione', en: 'Building application' },
        7: { it: 'Configurazione SSL', en: 'Configuring SSL' },
        8: { it: 'Creazione tabelle (Livello 0)', en: 'Creating tables (Level 0)' },
        9: { it: 'Creazione tabelle (Livello 1)', en: 'Creating tables (Level 1)' },
        10: { it: 'Creazione tabelle (Livello 2)', en: 'Creating tables (Level 2)' },
        11: { it: 'Creazione tabelle (Livello 3)', en: 'Creating tables (Level 3)' },
        12: { it: 'Creazione tabella versioning', en: 'Creating versioning table' },
        13: { it: 'Impostazione versione schema', en: 'Setting schema version' },
        14: { it: 'Avvio applicazione', en: 'Starting application' },
        15: { it: 'Verifica schema database', en: 'Verifying database schema' },
        16: { it: 'Inserimento dati iniziali', en: 'Inserting seed data' },
        17: { it: 'Creazione account amministratore', en: 'Creating admin account' },
        18: { it: 'Avvio Redis', en: 'Starting Redis' },
        19: { it: 'Copia frontend', en: 'Copying frontend files' },
        20: { it: 'Verifica applicazione', en: 'Health check' },
        21: { it: 'Generazione documento configurazione', en: 'Generating config document' },
        22: { it: 'Completamento installazione', en: 'Completing installation' }
    };

    // ==========================================
    // TRANSLATION SYSTEM
    // ==========================================

    async function loadTranslations(lang) {
        try {
            const response = await fetch(`/static/translations/${lang}.json`);
            if (!response.ok) throw new Error('Translation file not found');
            translations = await response.json();
            applyTranslations();
        } catch (error) {
            console.error('Failed to load translations:', error);
        }
    }

    function applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const text = getTranslation(key);
            if (text) {
                if (el.tagName === 'INPUT' && (el.type === 'text' || el.type === 'email')) {
                    el.placeholder = text;
                } else {
                    el.innerHTML = text;
                }
            }
        });
    }

    function getTranslation(key) {
        return key.split('.').reduce((obj, k) => obj && obj[k], translations) || null;
    }

    function t(key, fallback) {
        return getTranslation(key) || fallback || key;
    }

    // ==========================================
    // NAVIGATION
    // ==========================================

    function goToStep(step) {
        for (let i = 0; i < TOTAL_SCREENS; i++) {
            const el = document.getElementById(`step-${i}`);
            if (el) el.classList.add('hidden');
        }

        const target = document.getElementById(`step-${step}`);
        if (target) {
            target.classList.remove('hidden');
            currentStep = step;
        }

        // Stepper visibility
        const stepper = document.getElementById('wizard-stepper');
        if (stepper) {
            if (step <= 1 || step === 7) {
                stepper.classList.add('hidden');
            } else {
                stepper.classList.remove('hidden');
                updateStepper(step);
            }
        }

        window.scrollTo({ top: 0, behavior: 'smooth' });

        // Step-specific actions
        if (step === 5) populateSummary();
        if (step === 7) populateCompletion();
    }

    function updateStepper(activeStep) {
        const steps = document.querySelectorAll('.wizard-stepper .step');
        const connectors = document.querySelectorAll('.wizard-stepper .step-connector');

        steps.forEach(stepEl => {
            const stepNum = parseInt(stepEl.getAttribute('data-step'));
            stepEl.classList.remove('active', 'completed');
            if (stepNum === activeStep) {
                stepEl.classList.add('active');
            } else if (stepNum < activeStep) {
                stepEl.classList.add('completed');
            }
        });

        connectors.forEach((conn, index) => {
            const nextStep = steps[index + 1];
            if (nextStep) {
                const nextStepNum = parseInt(nextStep.getAttribute('data-step'));
                conn.classList.toggle('completed', nextStepNum <= activeStep);
            }
        });
    }

    // ==========================================
    // LANGUAGE SELECTION (Step 0)
    // ==========================================

    async function setLanguage(lang) {
        language = lang;
        document.documentElement.lang = lang;
        await loadTranslations(lang);
        goToStep(1);
    }

    // ==========================================
    // LOGIN (Step 1)
    // ==========================================

    async function login() {
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        const errorBox = document.getElementById('login-error');
        errorBox.classList.add('hidden');

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await response.json();

            if (response.ok && data.token) {
                sessionToken = data.token;
                goToStep(2);
                detectNetwork();
            } else {
                errorBox.classList.remove('hidden');
                shakeElement(errorBox);
            }
        } catch (error) {
            errorBox.classList.remove('hidden');
            shakeElement(errorBox);
        }
    }

    // ==========================================
    // NETWORK CONFIGURATION (Step 2)
    // ==========================================

    let networkMode = 'auto';

    function setNetworkMode(mode) {
        networkMode = mode;
        const buttons = document.querySelectorAll('#network-mode-toggle .toggle-btn');
        buttons.forEach(btn => btn.classList.remove('active'));
        if (mode === 'auto') {
            buttons[0].classList.add('active');
            detectNetwork();
        } else {
            buttons[1].classList.add('active');
            document.getElementById('network-auto-status').classList.add('hidden');
        }
    }

    async function detectNetwork() {
        try {
            const response = await fetch('/api/network/detect', {
                headers: { 'Authorization': `Bearer ${sessionToken}` }
            });
            if (!response.ok) throw new Error('Detection failed');
            const data = await response.json();

            document.getElementById('net-interface').value = data.interface || '';
            document.getElementById('net-subnet').value = data.subnet || '';
            document.getElementById('net-gateway').value = data.gateway || '';
            document.getElementById('net-ip-app').value = data.suggested_ips ? data.suggested_ips[0] : '';
            document.getElementById('net-ip-db').value = data.suggested_ips ? data.suggested_ips[1] : '';
            document.getElementById('net-ip-redis').value = data.suggested_ips ? data.suggested_ips[2] : '';

            document.getElementById('network-auto-status').classList.remove('hidden');
        } catch (error) {
            console.error('Network detection failed:', error);
            document.getElementById('network-auto-status').classList.add('hidden');
        }
    }

    function isValidIP(ip) {
        const parts = ip.split('.');
        if (parts.length !== 4) return false;
        return parts.every(p => {
            const num = parseInt(p, 10);
            return !isNaN(num) && num >= 0 && num <= 255 && p === num.toString();
        });
    }

    function isValidSubnet(cidr) {
        const parts = cidr.split('/');
        if (parts.length !== 2) return false;
        if (!isValidIP(parts[0])) return false;
        const mask = parseInt(parts[1], 10);
        return !isNaN(mask) && mask >= 1 && mask <= 32;
    }

    // ==========================================
    // PASSWORD VALIDATION
    // ==========================================

    function checkPasswordStrength(password) {
        const checks = {
            length: password.length >= PASSWORD_MIN_LENGTH,
            upper: /[A-Z]/.test(password),
            lower: /[a-z]/.test(password),
            number: /[0-9]/.test(password),
            symbol: /[^A-Za-z0-9]/.test(password)
        };
        const passed = Object.values(checks).filter(Boolean).length;
        let strength = 'weak';
        if (passed >= 4) strength = 'medium';
        if (passed === 5) strength = 'strong';
        return { checks, strength, passed, valid: passed === 5 };
    }

    function updatePasswordUI(inputId, strengthId, labelId, checklistId) {
        const input = document.getElementById(inputId);
        const password = input.value;
        const result = checkPasswordStrength(password);

        const strengthEl = document.getElementById(strengthId);
        strengthEl.className = 'wizard-password-strength';
        if (password.length > 0) strengthEl.classList.add(result.strength);

        const labelEl = document.getElementById(labelId);
        if (password.length > 0) {
            const labels = {
                weak: t('password.weak', 'Weak'),
                medium: t('password.medium', 'Medium'),
                strong: t('password.strong', 'Strong')
            };
            labelEl.textContent = labels[result.strength];
            labelEl.className = 'wizard-password-strength-label ' + result.strength;
        } else {
            labelEl.textContent = '';
        }

        const checklistEl = document.getElementById(checklistId);
        if (checklistEl) {
            checklistEl.querySelectorAll('.check-item').forEach(item => {
                const check = item.getAttribute('data-check');
                item.classList.toggle('passed', result.checks[check]);
            });
        }
        return result;
    }

    function initPasswordListeners() {
        const fields = [
            { input: 'db-password', strength: 'db-password-strength', label: 'db-password-strength-label', checklist: 'db-password-checklist' },
            { input: 'db-root-password', strength: 'db-root-strength', label: 'db-root-strength-label', checklist: 'db-root-checklist' },
            { input: 'admin-password', strength: 'admin-password-strength', label: 'admin-password-strength-label', checklist: 'admin-password-checklist' }
        ];
        fields.forEach(field => {
            const el = document.getElementById(field.input);
            if (el) {
                el.addEventListener('input', () => updatePasswordUI(field.input, field.strength, field.label, field.checklist));
            }
        });

        const confirmEl = document.getElementById('admin-password-confirm');
        if (confirmEl) {
            confirmEl.addEventListener('input', () => {
                const password = document.getElementById('admin-password').value;
                const confirm = confirmEl.value;
                if (confirm.length > 0 && password !== confirm) {
                    showFieldError('admin-password-confirm', t('admin.error_password_mismatch', 'Passwords do not match'));
                } else {
                    clearFieldError('admin-password-confirm');
                }
            });
        }
    }

    // ==========================================
    // USERNAME SUGGESTION (Step 4)
    // ==========================================

    function suggestUsername() {
        const firstname = document.getElementById('admin-firstname').value.trim().toLowerCase();
        const lastname = document.getElementById('admin-lastname').value.trim().toLowerCase();
        const usernameField = document.getElementById('admin-username');
        if (firstname && lastname) {
            const clean = (str) => str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, '');
            usernameField.value = clean(firstname) + '.' + clean(lastname);
        }
    }

    // ==========================================
    // VALIDATION & NAVIGATION
    // ==========================================

    async function validateAndNext(fromStep) {
        let valid = true;
        if (fromStep === 2) valid = await validateNetworkStep();
        else if (fromStep === 3) valid = validateDatabaseStep();
        else if (fromStep === 4) valid = validateAdminStep();

        if (valid) {
            saveStepData(fromStep);
            goToStep(fromStep + 1);
        }
    }

    async function validateNetworkStep() {
        let valid = true;
        const iface = document.getElementById('net-interface').value.trim();
        const subnet = document.getElementById('net-subnet').value.trim();
        const gateway = document.getElementById('net-gateway').value.trim();
        const ipApp = document.getElementById('net-ip-app').value.trim();
        const ipDb = document.getElementById('net-ip-db').value.trim();
        const ipRedis = document.getElementById('net-ip-redis').value.trim();
        const port = parseInt(document.getElementById('net-port').value);

        if (!iface) { showFieldError('net-interface', t('network.error_required', 'Required')); valid = false; }
        if (!isValidSubnet(subnet)) { showFieldError('net-subnet', t('network.error_subnet', 'Invalid subnet format (e.g. 10.0.0.0/24)')); valid = false; }
        if (!isValidIP(gateway)) { showFieldError('net-gateway', t('network.error_ip', 'Invalid IP address')); valid = false; }
        if (!isValidIP(ipApp)) { showFieldError('net-ip-app', t('network.error_ip', 'Invalid IP address')); valid = false; }
        if (!isValidIP(ipDb)) { showFieldError('net-ip-db', t('network.error_ip', 'Invalid IP address')); valid = false; }
        if (!isValidIP(ipRedis)) { showFieldError('net-ip-redis', t('network.error_ip', 'Invalid IP address')); valid = false; }
        if (isNaN(port) || port < 1024 || port > 65535) { showFieldError('net-port', t('network.error_port', 'Port must be between 1024 and 65535')); valid = false; }

        // Check for duplicate IPs
        const ips = [ipApp, ipDb, ipRedis];
        if (new Set(ips).size !== ips.length) {
            showFieldError('net-ip-redis', t('network.error_duplicate', 'Each service must have a unique IP'));
            valid = false;
        }

        return valid;
    }

    function validateDatabaseStep() {
        let valid = true;
        const name = document.getElementById('db-name').value.trim();
        const user = document.getElementById('db-user').value.trim();
        const password = document.getElementById('db-password').value;
        const rootPassword = document.getElementById('db-root-password').value;

        if (!name || name.length < 2) { showFieldError('db-name', t('database.error_name', 'At least 2 characters')); valid = false; }
        if (!user || user.length < 2) { showFieldError('db-user', t('database.error_user', 'At least 2 characters')); valid = false; }
        if (!checkPasswordStrength(password).valid) { showFieldError('db-password', t('database.error_password', 'Password does not meet requirements')); valid = false; }
        if (!checkPasswordStrength(rootPassword).valid) { showFieldError('db-root-password', t('database.error_root_password', 'Password does not meet requirements')); valid = false; }
        if (password === rootPassword) { showFieldError('db-root-password', t('database.error_same_password', 'Root password must differ from application password')); valid = false; }

        return valid;
    }

    function validateAdminStep() {
        let valid = true;
        const firstname = document.getElementById('admin-firstname').value.trim();
        const lastname = document.getElementById('admin-lastname').value.trim();
        const email = document.getElementById('admin-email').value.trim();
        const username = document.getElementById('admin-username').value.trim();
        const password = document.getElementById('admin-password').value;
        const confirm = document.getElementById('admin-password-confirm').value;

        if (!firstname || firstname.length < 2) { showFieldError('admin-firstname', t('admin.error_firstname', 'At least 2 characters')); valid = false; }
        if (!lastname || lastname.length < 2) { showFieldError('admin-lastname', t('admin.error_lastname', 'At least 2 characters')); valid = false; }
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { showFieldError('admin-email', t('admin.error_email', 'Invalid email')); valid = false; }
        if (!username || username.length < 4 || !/^[a-zA-Z0-9._]+$/.test(username)) { showFieldError('admin-username', t('admin.error_username', 'Min 4 chars, letters/numbers/dots/underscores')); valid = false; }
        if (!checkPasswordStrength(password).valid) { showFieldError('admin-password', t('admin.error_weak_password', 'Password does not meet requirements')); valid = false; }
        if (password !== confirm) { showFieldError('admin-password-confirm', t('admin.error_password_mismatch', 'Passwords do not match')); valid = false; }

        return valid;
    }

    // ==========================================
    // SAVE STEP DATA
    // ==========================================

    function saveStepData(step) {
        if (step === 2) {
            config.network = {
                interface: document.getElementById('net-interface').value.trim(),
                subnet: document.getElementById('net-subnet').value.trim(),
                gateway: document.getElementById('net-gateway').value.trim(),
                ip_app: document.getElementById('net-ip-app').value.trim(),
                ip_db: document.getElementById('net-ip-db').value.trim(),
                ip_redis: document.getElementById('net-ip-redis').value.trim(),
                port: document.getElementById('net-port').value.trim()
            };
            config.protocol = document.getElementById('net-protocol').value;
        } else if (step === 3) {
            config.database = {
                name: document.getElementById('db-name').value.trim(),
                user: document.getElementById('db-user').value.trim(),
                password: document.getElementById('db-password').value,
                root_password: document.getElementById('db-root-password').value
            };
        } else if (step === 4) {
            config.admin = {
                firstname: document.getElementById('admin-firstname').value.trim(),
                lastname: document.getElementById('admin-lastname').value.trim(),
                email: document.getElementById('admin-email').value.trim(),
                username: document.getElementById('admin-username').value.trim(),
                password: document.getElementById('admin-password').value
            };
        }
    }

    // ==========================================
    // SUMMARY (Step 5)
    // ==========================================

    function populateSummary() {
        const container = document.getElementById('summary-content');
        const n = config.network;
        const d = config.database;
        const a = config.admin;
        const url = `${config.protocol}://${n.ip_app}:${n.port}`;

        container.innerHTML = `
            <div class="wizard-summary-section">
                <h3>${t('summary.section_network', 'Rete')}</h3>
                ${summaryRow(t('network.interface', 'Interfaccia'), n.interface)}
                ${summaryRow(t('network.subnet', 'Subnet'), n.subnet)}
                ${summaryRow(t('network.gateway', 'Gateway'), n.gateway)}
                ${summaryRow(t('network.ip_app', 'IP Applicazione'), n.ip_app)}
                ${summaryRow(t('network.ip_db', 'IP Database'), n.ip_db)}
                ${summaryRow(t('network.ip_redis', 'IP Cache'), n.ip_redis)}
                ${summaryRow(t('network.port', 'Porta'), n.port)}
                ${summaryRow(t('network.protocol', 'Protocollo'), config.protocol.toUpperCase())}
                ${summaryRow(t('summary.url', 'URL di accesso'), url)}
            </div>
            <div class="wizard-summary-section">
                <h3>${t('summary.section_database', 'Database')}</h3>
                ${summaryRow(t('database.db_name', 'Nome database'), d.name)}
                ${summaryRow(t('database.db_user', 'Utente applicativo'), d.user)}
                ${summaryRow(t('database.db_password', 'Password applicativo'), '••••••••••••')}
                ${summaryRow(t('database.root_password', 'Password root'), '••••••••••••')}
            </div>
            <div class="wizard-summary-section">
                <h3>${t('summary.section_admin', 'Amministratore')}</h3>
                ${summaryRow(t('admin.first_name', 'Nome'), a.firstname)}
                ${summaryRow(t('admin.last_name', 'Cognome'), a.lastname)}
                ${summaryRow(t('admin.email', 'Email'), a.email)}
                ${summaryRow(t('admin.username', 'Nome utente'), a.username)}
                ${summaryRow(t('admin.password', 'Password'), '••••••••••••')}
            </div>
        `;
    }

    function summaryRow(label, value) {
        return `<div class="wizard-summary-row"><span class="label">${label}</span><span class="value">${value}</span></div>`;
    }

    // ==========================================
    // DOWNLOAD CONFIG DOCUMENT
    // ==========================================

    function downloadConfig() {
        const includePassword = document.getElementById('summary-include-password').checked;
        const n = config.network;
        const d = config.database;
        const a = config.admin;
        const now = new Date();
        const dateStr = now.toLocaleDateString(language === 'it' ? 'it-IT' : 'en-US', {
            day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit'
        });
        const url = `${config.protocol}://${n.ip_app}:${n.port}`;

        let content = `
════════════════════════════════════════════════════
  IT ASSET MANAGER — ${t('document.title', 'SYSTEM CONFIGURATION')}
════════════════════════════════════════════════════

${t('document.install_date', 'Installation date')}:    ${dateStr}
${t('document.version', 'Application version')}:  IT Asset Manager v2.7.4

─── ${t('summary.section_network', 'NETWORK').toUpperCase()} ───

${t('network.interface', 'Interface')}:   ${n.interface}
Subnet:                ${n.subnet}
Gateway:               ${n.gateway}
IP App:                ${n.ip_app}
IP Database:           ${n.ip_db}
IP Redis:              ${n.ip_redis}
${t('network.port', 'Port')}:    ${n.port}
${t('network.protocol', 'Protocol')}:  ${config.protocol.toUpperCase()}

URL:  ${url}

─── DATABASE ───

${t('database.db_name', 'Database')}:         ${d.name}
${t('database.db_user', 'User')}:    ${d.user}
${t('database.db_password', 'Password')}:  ${d.password}
Root:         ${d.root_password}

─── ${t('summary.section_admin', 'ADMINISTRATOR').toUpperCase()} ───

${t('document.full_name', 'Name')}:         ${a.firstname} ${a.lastname}
Email:                 ${a.email}
Username:              ${a.username}
${includePassword ? `Password:              ${a.password}` : `Password:              [${t('document.not_included', 'not included')}]`}

════════════════════════════════════════════════════
⚠️ ${t('document.confidential', 'CONFIDENTIAL — Store securely')}
════════════════════════════════════════════════════
`.trim();

        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const blobUrl = URL.createObjectURL(blob);
        const a_el = document.createElement('a');
        a_el.href = blobUrl;
        a_el.download = `IT_Asset_Manager_Config_${now.toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a_el);
        a_el.click();
        document.body.removeChild(a_el);
        URL.revokeObjectURL(blobUrl);
    }

    // ==========================================
    // INSTALLATION (Step 6) — 22 API steps
    // ==========================================

    function confirmInstall() {
        document.getElementById('confirm-modal').classList.add('visible');
    }

    function closeModal() {
        document.getElementById('confirm-modal').classList.remove('visible');
    }

    function getStepName(stepNum) {
        const names = INSTALL_STEP_NAMES[stepNum];
        if (!names) return `Step ${stepNum}`;
        return language === 'it' ? names.it : names.en;
    }

    function buildInstallStepsList() {
        const container = document.getElementById('install-steps-list');
        container.innerHTML = '';
        for (let i = 1; i <= TOTAL_INSTALL_STEPS; i++) {
            const row = document.createElement('div');
            row.className = 'install-step-row';
            row.id = `install-step-row-${i}`;
            row.innerHTML = `
                <span class="install-step-number">${i}</span>
                <span class="install-step-name">${getStepName(i)}</span>
                <span class="install-step-status" id="install-step-status-${i}">⏳</span>
            `;
            container.appendChild(row);
        }
    }

    function updateInstallStepStatus(stepNum, status) {
        const statusEl = document.getElementById(`install-step-status-${stepNum}`);
        const rowEl = document.getElementById(`install-step-row-${stepNum}`);
        if (!statusEl || !rowEl) return;

        rowEl.classList.remove('running', 'success', 'error');

        if (status === 'running') {
            statusEl.textContent = '⏳';
            rowEl.classList.add('running');
            rowEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else if (status === 'success') {
            statusEl.textContent = '✅';
            rowEl.classList.add('success');
        } else if (status === 'error') {
            statusEl.textContent = '❌';
            rowEl.classList.add('error');
        }
    }

    function addLogEntry(message, type) {
        const log = document.getElementById('install-log');
        const time = new Date().toLocaleTimeString();
        const iconMap = { info: '⏳', success: '✅', error: '❌' };
        const icon = iconMap[type] || '•';

        const entry = document.createElement('div');
        entry.className = `log-entry ${type || 'info'}`;
        entry.innerHTML = `<span class="log-time">${time}</span><span class="log-icon">${icon}</span><span>${message}</span>`;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }

    function updateProgress(stepNum) {
        const percent = Math.round((stepNum / TOTAL_INSTALL_STEPS) * 100);
        document.getElementById('install-progress-fill').style.width = percent + '%';
        document.getElementById('install-progress-percent').textContent = percent + '%';
        document.getElementById('install-progress-step').textContent = getStepName(stepNum);
    }

    async function startInstall() {
        closeModal();
        goToStep(6);
        lastFailedStep = 0;

        // Reset UI
        document.getElementById('install-error').classList.add('hidden');
        document.getElementById('install-log').innerHTML = '';
        document.getElementById('install-progress-fill').style.width = '0%';
        document.getElementById('install-progress-percent').textContent = '0%';
        document.getElementById('install-progress-step').textContent = t('install.preparing', 'Preparazione...');

        buildInstallStepsList();

        // Call /api/install/init
        addLogEntry(t('install.log_init', 'Inizializzazione installazione...'), 'info');
        try {
            const initResp = await fetch('/api/install/init', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${sessionToken}`
                },
                body: JSON.stringify(config)
            });
            const initData = await initResp.json();
            if (!initResp.ok || initData.status === 'error') {
                throw new Error(initData.message || 'Init failed');
            }
            addLogEntry(t('install.log_init_ok', 'Inizializzazione completata'), 'success');
        } catch (error) {
            addLogEntry(`${t('install.log_init_fail', 'Errore inizializzazione')}: ${error.message}`, 'error');
            document.getElementById('install-error-message').textContent = error.message;
            document.getElementById('install-error').classList.remove('hidden');
            return;
        }

        // Execute steps 1-22
        await executeStepsFrom(1);
    }

    async function executeStepsFrom(startStep) {
        for (let i = startStep; i <= TOTAL_INSTALL_STEPS; i++) {
            updateInstallStepStatus(i, 'running');
            updateProgress(i);
            addLogEntry(`${getStepName(i)}...`, 'info');

            try {
                const resp = await fetch(`/api/install/step/${i}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${sessionToken}` }
                });
                const data = await resp.json();

                if (!resp.ok || data.status === 'error') {
                    updateInstallStepStatus(i, 'error');
                    addLogEntry(`❌ ${data.message || 'Errore sconosciuto'}`, 'error');
                    lastFailedStep = i;
                    document.getElementById('install-error-message').textContent = data.message || 'Errore sconosciuto';
                    document.getElementById('install-error').classList.remove('hidden');
                    return;
                }

                updateInstallStepStatus(i, 'success');
                addLogEntry(`✅ ${data.message}`, 'success');

            } catch (error) {
                updateInstallStepStatus(i, 'error');
                addLogEntry(`❌ ${t('install.log_connection_error', 'Errore di connessione')}: ${error.message}`, 'error');
                lastFailedStep = i;
                document.getElementById('install-error-message').textContent = error.message;
                document.getElementById('install-error').classList.remove('hidden');
                return;
            }
        }

        // All done!
        updateProgress(TOTAL_INSTALL_STEPS);
        addLogEntry(t('install.log_complete', '🎉 Installazione completata con successo!'), 'success');
        setTimeout(() => goToStep(7), 2000);
    }

    async function retryInstall() {
        if (lastFailedStep > 0) {
            document.getElementById('install-error').classList.add('hidden');
            addLogEntry(t('install.log_retry', `Riprovo dallo step ${lastFailedStep}...`), 'info');
            await executeStepsFrom(lastFailedStep);
        } else {
            startInstall();
        }
    }

    // ==========================================
    // COMPLETION (Step 7)
    // ==========================================

    function populateCompletion() {
        const url = `${config.protocol}://${config.network.ip_app}:${config.network.port}`;
        document.getElementById('completion-url').textContent = url;
        document.getElementById('completion-link').href = url;
        document.getElementById('completion-username').textContent = config.admin.username;
    }

    async function openApp() {
        const url = `${config.protocol}://${config.network.ip_app}:${config.network.port}`;
        // Open app in new tab
        window.open(url, '_blank');
        // Cleanup wizard container
        try {
            await fetch('/api/cleanup', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${sessionToken}` }
            });
        } catch (e) {
            // Wizard is shutting down, connection error expected
        }
    }

    // ==========================================
    // UI HELPERS
    // ==========================================

    function showFieldError(fieldId, message) {
        const errorEl = document.getElementById(`${fieldId}-error`);
        const inputEl = document.getElementById(fieldId);
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.add('visible');
            errorEl.classList.remove('hidden');
        }
        if (inputEl) {
            inputEl.classList.add('error');
            inputEl.classList.remove('success');
        }
    }

    function clearFieldError(fieldId) {
        const errorEl = document.getElementById(`${fieldId}-error`);
        const inputEl = document.getElementById(fieldId);
        if (errorEl) {
            errorEl.classList.remove('visible');
            errorEl.classList.add('hidden');
        }
        if (inputEl) inputEl.classList.remove('error');
    }

    function shakeElement(el) {
        el.style.animation = 'none';
        el.offsetHeight;
        el.style.animation = 'shake 0.5s ease';
    }

    // Clear errors on focus
    document.addEventListener('focusin', (e) => {
        if (e.target.classList && e.target.classList.contains('wizard-input')) {
            clearFieldError(e.target.id);
        }
    });

    // Enter key on login
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && currentStep === 1) login();
    });

    // ==========================================
    // INITIALIZATION
    // ==========================================

    function init() {
        initPasswordListeners();
        goToStep(0);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // ==========================================
    // PUBLIC API
    // ==========================================

    return {
        setLanguage,
        login,
        goToStep,
        setNetworkMode,
        validateAndNext,
        suggestUsername,
        downloadConfig,
        confirmInstall,
        closeModal,
        startInstall,
        retryInstall,
        openApp
    };
})();
