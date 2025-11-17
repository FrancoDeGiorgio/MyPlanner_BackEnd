# 🚀 Quick Start - MyPlanner Backend

Guida rapida per iniziare subito dopo la migrazione.

---

## ⚡ Setup Rapido (5 minuti)

### 1. Verifica Python
```bash
python --version  # Dovrebbe essere 3.9+
```

### 2. Installa Dipendenze
```bash
cd MyPlanner_BackEnd
pip install -r requirements.txt
```

### 3. Configura Ambiente
Crea file `.env` nella root:
```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-super-secret-key-here-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. Avvia Server
```bash
uvicorn main:app --reload
```

### 5. Verifica Funzionamento
```bash
# Health check
curl http://localhost:8000/

# Documentazione interattiva
# Apri browser: http://localhost:8000/docs
```

---

## 📚 Comandi Utili

### Development
```bash
# Avvia con reload automatico
uvicorn main:app --reload

# Avvia su porta specifica
uvicorn main:app --port 8080

# Avvia con log dettagliati
uvicorn main:app --log-level debug
```

### Testing
```bash
# Tutti i test
pytest

# Solo integration
pytest tests/integration/

# Con coverage
pytest --cov=app --cov-report=html

# Verboso
pytest -v -s
```

### Docker
```bash
# Build immagine
docker build -t myplanner-backend .

# Run container
docker run -p 8000:8000 --env-file .env myplanner-backend

# Con Docker Compose
docker-compose up --build
```

### Database
```bash
# Connetti a PostgreSQL (locale)
psql -U postgres -d myplanner

# Verifica tabelle
psql -U postgres -d myplanner -c "\dt"

# Test connessione da Python
python -c "from app.core.database import get_db_conn; print('✅ DB OK')"
```

---

## 🧪 Test Rapido API

### 1. Registrazione Utente
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name_user": "testuser", "password": "testpass123"}'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

Salva il token ricevuto in una variabile:
```bash
TOKEN="<il-token-ricevuto>"
```

### 3. Crea Task
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name_task": "Mia prima task",
    "description_task": "Task di test",
    "date_time": "2025-11-10T10:00:00",
    "duration_minutes": 60
  }'
```

### 4. Lista Task
```bash
curl -X GET http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔍 Verifica Installazione

### Script Automatico
```bash
python .verification-script.py
```

### Verifica Manuale
```bash
# Test import
python -c "from main import app; print('✅ Main OK')"
python -c "from app.core import config; print('✅ Core OK')"
python -c "from app.services import auth_service; print('✅ Services OK')"
python -c "from app.repositories import user_repository; print('✅ Repositories OK')"
```

---

## 📖 Documentazione

### Locale
- **README**: `README.md`
- **Architettura**: `ARCHITECTURE_MIGRATION.md`
- **Cleanup**: `CLEANUP_COMPLETED.md`
- **Docs**: `docs/README.md`

### Online (server attivo)
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🐛 Troubleshooting

### Errore: "Module not found"
```bash
# Verifica di essere nella directory corretta
pwd  # Dovrebbe essere MyPlanner_BackEnd

# Reinstalla dipendenze
pip install -r requirements.txt
```

### Errore: "Database connection failed"
```bash
# Verifica .env
cat .env | grep DATABASE_URL

# Test connessione
python -c "from app.core.database import get_db_conn; print('✅ OK')"
```

### Errore: "Port already in use"
```bash
# Usa porta diversa
uvicorn main:app --port 8001

# Oppure trova e termina processo
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

### Import Errors
```bash
# Verifica struttura
python .verification-script.py

# Controlla __init__.py
ls app/*/__init__.py
```

---

## 🎯 Prossimi Passi

### 1. Sviluppo
- Leggi `docs/development/setup.md`
- Leggi `docs/development/contributing.md`
- Studia `docs/architecture/layers.md`

### 2. Testing
- Implementa test in `tests/unit/`
- Aggiungi test in `tests/integration/`
- Scrivi test E2E in `tests/e2e/`

### 3. Deployment
- Configura Docker production
- Setup CI/CD pipeline
- Deploy su Render/Heroku/Railway

---

## 🔗 Link Rapidi

| Risorsa | Link |
|---------|------|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/ |
| Docs Index | `docs/README.md` |
| Architecture | `ARCHITECTURE_MIGRATION.md` |
| Contributing | `docs/development/contributing.md` |

---

## 💡 Tips

- **Hot Reload**: Usa `--reload` durante sviluppo
- **Debug**: Aggiungi `import pdb; pdb.set_trace()` per breakpoint
- **Logs**: Controlla `app/utils/logger.py` per logging
- **Env**: Non committare mai `.env` (è in `.gitignore`)
- **Tests**: Scrivi test prima di committare
- **Docs**: Aggiorna docs con ogni modifica significativa

---

**Buon coding! 🚀🇮🇹**

