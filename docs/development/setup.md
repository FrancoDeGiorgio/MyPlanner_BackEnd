# Setup Ambiente di Sviluppo

**Ultimo aggiornamento**: 2025-11-06

Guida completa per configurare l'ambiente di sviluppo locale.

## 📋 Prerequisiti

### Software Richiesto
- **Python**: 3.11+ ([Download](https://www.python.org/downloads/))
- **PostgreSQL**: 14+ ([Download](https://www.postgresql.org/download/))
- **Git**: Ultima versione ([Download](https://git-scm.com/downloads))

### Software Opzionale (Consigliato)
- **Docker**: Per ambiente isolato ([Download](https://www.docker.com/))
- **VS Code**: Editor consigliato ([Download](https://code.visualstudio.com/))
- **Postman**: Per testare API ([Download](https://www.postman.com/downloads/))

## 🚀 Setup Rapido

### 1. Clone Repository
```bash
git clone https://github.com/your-org/MyPlanner.git
cd MyPlanner/MyPlanner_BackEnd
```

### 2. Virtual Environment
```bash
# Crea virtual environment
python -m venv venv

# Attiva (Windows)
venv\Scripts\activate

# Attiva (Linux/Mac)
source venv/bin/activate
```

### 3. Installa Dipendenze
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurazione Database

#### Opzione A: Database Locale

**Crea Database**:
```bash
psql -U postgres
```

```sql
CREATE DATABASE myplanner_dev;
CREATE USER myplanner_user WITH PASSWORD 'dev_password';
GRANT ALL PRIVILEGES ON DATABASE myplanner_dev TO myplanner_user;
```

**Configura URL**:
```bash
# .env
DATABASE_URL=postgresql://myplanner_user:dev_password@localhost:5432/myplanner_dev
SECRET_KEY=your-super-secret-key-change-in-production
```

#### Opzione B: Supabase (Consigliato)

1. Vai su [supabase.com](https://supabase.com/)
2. Crea nuovo progetto
3. Copia Connection String da Settings → Database
4. Configura `.env`:

```bash
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT].supabase.co:6543/postgres?sslmode=require&options=-c%20pool_timeout=0
SECRET_KEY=your-super-secret-key-change-in-production
```

### 5. Setup Database Schema

**Esegui Migration** (se configurato Alembic):
```bash
alembic upgrade head
```

**O esegui SQL manualmente**:
```sql
-- Tabella users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name_user VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabella tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(150) NOT NULL,
    description VARCHAR(255) NOT NULL,
    color VARCHAR(20) DEFAULT 'green',
    date_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_minutes INTEGER CHECK (duration_minutes >= 5 AND duration_minutes <= 1440),
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Policy per SELECT
CREATE POLICY tasks_tenant_isolation_select ON tasks
    FOR SELECT
    USING (tenant_id = get_current_tenant_id());

-- Policy per INSERT
CREATE POLICY tasks_tenant_isolation_insert ON tasks
    FOR INSERT
    WITH CHECK (tenant_id = get_current_tenant_id());

-- Policy per UPDATE
CREATE POLICY tasks_tenant_isolation_update ON tasks
    FOR UPDATE
    USING (tenant_id = get_current_tenant_id())
    WITH CHECK (tenant_id = get_current_tenant_id());

-- Policy per DELETE
CREATE POLICY tasks_tenant_isolation_delete ON tasks
    FOR DELETE
    USING (tenant_id = get_current_tenant_id());

-- Funzione helper per RLS
CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS UUID AS $$
    SELECT id FROM users 
    WHERE name_user = current_setting('request.jwt.claim.sub', true);
$$ LANGUAGE SQL STABLE;
```

### 6. Avvia Server
```bash
uvicorn main:app --reload
```

**Output atteso**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

### 7. Verifica Setup
```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

---

## 🐳 Setup con Docker (Alternativo)

### Docker Compose
```bash
# Build e avvia
docker-compose up --build

# In background
docker-compose up -d

# Logs
docker-compose logs -f backend

# Stop
docker-compose down
```

### Dockerfile Solo Backend
```bash
# Build
docker build -t myplanner-backend .

# Run
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="your-secret" \
  myplanner-backend
```

---

## ⚙️ Configurazione IDE

### VS Code

**Estensioni Consigliate**:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "tamasfe.even-better-toml",
    "ms-azuretools.vscode-docker"
  ]
}
```

**Settings** (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.rulers": [100]
}
```

**Launch Configuration** (`.vscode/launch.json`):
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

---

## 🧪 Setup Testing

### Install Test Dependencies
```bash
pip install pytest pytest-cov pytest-asyncio httpx
```

### Run Tests
```bash
# Tutti i test
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Solo unit tests
pytest tests/unit

# Con output verboso
pytest -v

# Stop al primo fallimento
pytest -x
```

### Test Configuration (`pytest.ini`)
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
```

---

## 🔧 Tools Aggiuntivi

### Linting
```bash
# Flake8
flake8 app/ --max-line-length=100

# Black (formatter)
black app/ tests/

# isort (import sorting)
isort app/ tests/
```

### Type Checking
```bash
# mypy
mypy app/
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**`.pre-commit-config.yaml`**:
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

---

## 📚 Risorse Utili

### Documentazione
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- PostgreSQL: https://www.postgresql.org/docs/
- Supabase: https://supabase.com/docs

### Tutorial Interni
- [Architettura Overview](../architecture/overview.md)
- [Contributing Guide](contributing.md)
- [API Authentication](../api/authentication.md)

---

## ⚠️ Troubleshooting

### Errore: "ModuleNotFoundError"
**Soluzione**: Verifica virtual environment attivo e dipendenze installate
```bash
pip install -r requirements.txt
```

### Errore: "Connection refused" (Database)
**Soluzione**: Verifica PostgreSQL in esecuzione
```bash
# Windows
sc query postgresql-x64-14

# Linux
systemctl status postgresql
```

### Errore: "Permission denied" (Database)
**Soluzione**: Verifica credenziali in `.env`

### Errore: "Port 8000 already in use"
**Soluzione**: Cambia porta o killa processo
```bash
# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 📧 Supporto

Per problemi di setup:
1. Controlla questa guida
2. Cerca negli issue GitHub
3. Chiedi nel team

---

**Next**: [Testing Guide](testing.md) | [Contributing](contributing.md)

