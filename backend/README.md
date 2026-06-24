# Asset Management Backend

Backend FastAPI per IT Asset Manager.

## Password Hashing

**Algoritmo**: Argon2 (passlib[argon2] + argon2-cffi)

- Nessun bcrypt utilizzato
- Password minimo 8 caratteri
- Validazione automatica in `app/core/security.py`

## Dipendenze

Vedi `pyproject.toml` per l'elenco completo.

**Password hashing**:
- `passlib[argon2]>=1.7.4`
- `argon2-cffi>=23.1.0`

## Setup

1. Copia `env.example` in `.env` e configura:
   - `ADMIN_USERNAME` (obbligatorio)
   - `ADMIN_PASSWORD` (obbligatorio, minimo 8 caratteri)
   - `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

2. Build Docker:
   ```bash
   docker build -t asset-backend .
   ```

3. Avvio:
   ```bash
   docker run -p 8000:8000 --env-file .env asset-backend
   ```

## Seed Admin

Il seed admin viene eseguito automaticamente all'avvio:
- Valida `ADMIN_USERNAME` e `ADMIN_PASSWORD`
- Se invalidi: errore chiaro + exit(1)
- Se utente esiste: log "[seed] admin already exists: <username>"
- Se creato: log "[seed] admin created: <username>"

