# 🗓️ MyPlanner Backend

Backend API per MyPlanner - Sistema di gestione task multi-tenant con Row-Level Security.

**Versione**: 2.0.0  
**Architettura**: Layer-based moderna  
**Framework**: FastAPI + PostgreSQL + Supabase RLS

---

## 🚀 Quick Start

```bash
# 1. Clone e naviga
cd MyPlanner_BackEnd

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Configura ambiente
cp .env.example .env
# Edita .env con DATABASE_URL e SECRET_KEY

# 4. Avvia server
uvicorn main:app --reload

# 5. Apri documentazione
open http://localhost:8000/docs
```

---

## 📁 Struttura Progetto

```
app/
├── api/              # 🌐 Presentation Layer (routes, middleware)
├── services/         # 💼 Business Logic Layer
├── repositories/     # 💾 Data Access Layer (RLS)
├── models/           # 🎯 Domain Models
├── schemas/          # 📋 DTO (Pydantic)
├── core/             # ⚙️ Infrastructure (config, security, DB)
└── utils/            # 🛠️ Utilities (logger, decorators)

tests/
├── unit/             # 🧪 Test unitari
├── integration/      # 🔗 Test integrazione
└── e2e/             # 🌍 Test end-to-end

docs/                 # 📚 Documentazione completa
```

---

## ✨ Features

- ✅ **Autenticazione JWT** - Login sicuro con token Bearer
- ✅ **Multi-Tenancy** - Isolamento dati tra utenti con RLS
- ✅ **CRUD Task** - Gestione completa attività
- ✅ **API REST** - Endpoint documentati con OpenAPI
- ✅ **Layer Architecture** - Codice organizzato e manutenibile
- ✅ **Type Safety** - Type hints completi
- ✅ **Documentazione 100%** - Docstring in italiano

---

## 📖 Documentazione

### Guide Principali
- **[Panoramica Architettura](docs/architecture/overview.md)** - Struttura e design
- **[Setup Ambiente](docs/development/setup.md)** - Configurazione sviluppo
- **[API Authentication](docs/api/authentication.md)** - Endpoint auth
- **[Contributing Guide](docs/development/contributing.md)** - Come contribuire
- **[Migrazione](ARCHITECTURE_MIGRATION.md)** - Storia migrazione architettura

### ADR (Architecture Decision Records)
- **[ADR 001](docs/adr/001-layered-architecture.md)** - Scelta architettura a layer

---

## 🏗️ Architettura

### Layer Pattern

```
Router (API) → Service (Business Logic) → Repository (Data Access) → Database
     ↓              ↓                          ↓
  Schemas        Models                     Utils/Core
```

### Principi
- **Separation of Concerns** - Ogni layer ha responsabilità specifiche
- **Dependency Inversion** - Layer superiori dipendono da astrazioni
- **Single Responsibility** - Ogni modulo ha un solo scopo
- **DRY** - Codice condiviso in utilities e base classes

---

## 🔐 Sicurezza

### Multi-Tenancy con RLS
- **Row-Level Security** a livello PostgreSQL
- Policy database isolano dati per tenant
- Context JWT configurato automaticamente
- Decorator `@with_rls_context` per repository

### Autenticazione
- Token JWT con HS256
- Password hashate con bcrypt
- Scadenza configurabile (default 30 min)
- OAuth2 Password Bearer Flow

---

## 🧪 Testing

```bash
# Tutti i test
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Solo integration
pytest tests/integration/

# Verboso
pytest -v
```

---

## 🐳 Docker

### Setup Automatico

```bash
# Build e avvia (database auto-inizializzato!)
docker-compose up -d

# Verifica inizializzazione
docker-compose logs db | grep "INIZIALIZZATO"
```

**✨ Il database viene inizializzato automaticamente** con:
- Tabelle `users` e `tasks`
- Indici per performance
- Trigger `updated_at`
- Permessi e ruoli
- Vincoli di integrità

📚 **Documentazione completa**: `db/README.md`

### Reset Database

```bash
# Ferma e rimuovi tutto (incluso DB)
docker-compose down -v

# Riavvia (DB viene ricreato)
docker-compose up -d
```

### Solo Backend

```bash
docker build -t myplanner-backend .
docker run -p 8000:8000 --env-file .env myplanner-backend
```

---

## 📊 API Endpoints

### Authentication
- `POST /auth/register` - Registrazione nuovo utente
- `POST /auth/login` - Login con JWT token

### Tasks (Protected)
- `GET /tasks` - Lista task utente
- `POST /tasks` - Crea nuova task
- `PUT /tasks/{id}` - Aggiorna task
- `DELETE /tasks/{id}` - Elimina task

### Documentazione Interattiva
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🛠️ Stack Tecnologico

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 14+ (Supabase)
- **ORM**: psycopg2 (raw SQL con RLS)
- **Auth**: JWT (python-jose)
- **Validation**: Pydantic v2
- **Testing**: pytest
- **Docs**: OpenAPI/Swagger

---

## 📝 Development

### Code Style
- **PEP 8** compliant
- **Type hints** obbligatori
- **Docstring** in italiano
- **Max line length**: 100 caratteri

### Workflow
1. Crea branch feature
2. Implementa modifiche
3. Aggiungi test
4. Aggiorna docs
5. PR con review

### Pre-commit
```bash
# Install
pip install pre-commit
pre-commit install

# Run
pre-commit run --all-files
```

---

## 🚢 Deployment

### Render
Vedi [docs/deployment/render.md](docs/deployment/render.md)

### Docker
Vedi [docs/deployment/docker.md](docs/deployment/docker.md)

### Variabili d'Ambiente
```env
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-secret-jwt-key
ENVIRONMENT=production
DEBUG=False
```

---

## 📈 Roadmap

- [ ] **Alembic migrations** - Gestione schema database
- [ ] **Rate limiting** - Throttling richieste
- [ ] **Redis cache** - Cache layer per performance
- [ ] **WebSockets** - Aggiornamenti real-time
- [ ] **Email service** - Notifiche via email
- [ ] **File upload** - Allegati task

---

## 🤝 Contributing

Leggi [CONTRIBUTING.md](docs/development/contributing.md) per:
- Code style guidelines
- Processo PR
- Checklist commit
- Best practices

---

## 📜 License

Proprietario - MyPlanner Team

---

## 📧 Supporto

- **Docs**: Controlla `/docs` per guide dettagliate
- **Issues**: Apri issue su GitHub
- **Team**: Contatta il team di sviluppo

---

## 🎉 Credits

Sviluppato con ❤️ dal team MyPlanner

**Versione 2.0.0** - Migrazione architettura completata il 2025-11-06

---

**Happy Coding! 🚀**
