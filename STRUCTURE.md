# 📁 Struttura Progetto MyPlanner Backend

Visualizzazione completa della struttura dopo la migrazione.

---

## 🌳 Albero Completo

```
MyPlanner_BackEnd/
│
├── 📄 main.py                                # 🚀 Entry point FastAPI
├── 📄 requirements.txt                        # 📦 Dipendenze Python
├── 📄 runtime.txt                             # 🐍 Versione Python
├── 📄 Dockerfile                              # 🐳 Container config
├── 📄 .gitignore                              # 🚫 File da ignorare
│
├── 📄 README.md                               # 📖 Documentazione principale
├── 📄 QUICK_START.md                          # ⚡ Guida rapida
├── 📄 ARCHITECTURE_MIGRATION.md               # 🏗️ Storia migrazione
├── 📄 CLEANUP_COMPLETED.md                    # 🧹 Report cleanup
├── 📄 FINAL_SUMMARY.md                        # 🎉 Riepilogo finale
├── 📄 STRUCTURE.md                            # 📁 Questo file
│
├── 📂 app/                                    # 🎯 APPLICAZIONE PRINCIPALE
│   ├── __init__.py                           # Package root
│   │
│   ├── 📂 api/                               # 🌐 PRESENTATION LAYER
│   │   ├── __init__.py
│   │   ├── dependencies.py                   # Dependency Injection (get_current_user)
│   │   │
│   │   ├── 📂 routes/                        # Router endpoint
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                       # POST /auth/register, /auth/login
│   │   │   └── tasks.py                      # CRUD /tasks
│   │   │
│   │   └── 📂 middleware/                    # Middleware HTTP
│   │       ├── __init__.py
│   │       ├── cors.py                       # CORS configuration
│   │       └── error_handler.py              # Error handling globale
│   │
│   ├── 📂 services/                          # 💼 BUSINESS LOGIC LAYER
│   │   ├── __init__.py
│   │   ├── auth_service.py                   # Logica autenticazione
│   │   └── task_service.py                   # Logica gestione task
│   │
│   ├── 📂 repositories/                      # 💾 DATA ACCESS LAYER
│   │   ├── __init__.py
│   │   ├── base_repository.py                # Abstract base repository
│   │   ├── user_repository.py                # Query utenti
│   │   └── task_repository.py                # Query task con RLS
│   │
│   ├── 📂 models/                            # 🎯 DOMAIN MODELS
│   │   ├── __init__.py
│   │   ├── user.py                           # Dataclass User
│   │   └── task.py                           # Dataclass Task
│   │
│   ├── 📂 schemas/                           # 📋 DTO LAYER (Pydantic)
│   │   ├── __init__.py
│   │   ├── auth.py                           # UserCreate, Token
│   │   └── task.py                           # TaskCreate, TaskUpdate, TaskResponse
│   │
│   ├── 📂 core/                              # ⚙️ INFRASTRUCTURE
│   │   ├── __init__.py
│   │   ├── config.py                         # Configurazione (.env, settings)
│   │   ├── database.py                       # Database connection + RLS
│   │   ├── security.py                       # Password hashing + JWT
│   │   └── exceptions.py                     # Custom exceptions
│   │
│   ├── 📂 utils/                             # 🛠️ UTILITIES
│   │   ├── __init__.py
│   │   ├── decorators.py                     # @with_rls_context
│   │   ├── logger.py                         # Logging utilities
│   │   └── validators.py                     # Validation functions
│   │
│   └── 📂 migrations/                        # 🔄 DATABASE MIGRATIONS
│       └── (vuoto - pronto per Alembic)
│
├── 📂 tests/                                 # 🧪 TEST SUITE
│   ├── __init__.py
│   ├── conftest.py                           # Pytest fixtures
│   │
│   ├── 📂 unit/                              # Test unitari
│   │   └── __init__.py
│   │
│   ├── 📂 integration/                       # Test integrazione
│   │   ├── __init__.py
│   │   ├── test_auth_flow.py                # Test autenticazione completa
│   │   └── test_task_crud.py                # Test CRUD task + RLS
│   │
│   └── 📂 e2e/                               # Test end-to-end
│       └── __init__.py
│
└── 📂 docs/                                  # 📚 DOCUMENTAZIONE
    ├── README.md                             # Indice documentazione
    │
    ├── 📂 architecture/                      # Architettura
    │   ├── overview.md                       # Panoramica generale
    │   └── layers.md                         # Dettaglio layer pattern
    │
    ├── 📂 api/                               # Documentazione API
    │   └── authentication.md                 # Endpoint autenticazione
    │
    ├── 📂 development/                       # Guide sviluppo
    │   ├── setup.md                          # Setup ambiente
    │   └── contributing.md                   # Linee guida contribuzione
    │
    ├── 📂 deployment/                        # Guide deployment
    │   └── (vuoto - pronto per guide)
    │
    └── 📂 adr/                               # Architecture Decision Records
        └── 001-layered-architecture.md       # ADR migrazione layer
```

---

## 📊 Statistiche per Layer

| Layer | File | Linee Codice* | Responsabilità |
|-------|------|---------------|----------------|
| **API** | 5 | ~600 | HTTP, routing, validazione I/O |
| **Services** | 2 | ~400 | Business logic, orchestrazione |
| **Repositories** | 3 | ~500 | SQL queries, RLS, transazioni |
| **Models** | 2 | ~150 | Domain entities |
| **Schemas** | 2 | ~300 | DTO, validazione Pydantic |
| **Core** | 4 | ~700 | Config, security, DB, exceptions |
| **Utils** | 3 | ~350 | Decorators, logger, validators |
| **Tests** | 2 | ~200 | Integration tests |
| **Docs** | 7 | ~3000 | Documentazione completa |

*\*Include commenti e docstring*

---

## 🔄 Flusso di Esecuzione Tipico

### Esempio: Creazione Task

```
1. Client HTTP
   ↓
2. FastAPI (main.py)
   ↓
3. API Layer (routes/tasks.py)
   - Riceve richiesta POST /tasks
   - Valida TaskCreate schema
   - Estrae current_user da JWT
   ↓
4. Service Layer (services/task_service.py)
   - Recupera tenant_id da username
   - Valida business rules
   - Chiama repository
   ↓
5. Repository Layer (repositories/task_repository.py)
   - Applica RLS context (@with_rls_context)
   - Esegue INSERT SQL
   - Commit transazione
   ↓
6. Database (PostgreSQL + RLS)
   - Verifica policy RLS
   - Inserisce record
   - Ritorna ID
   ↓
7. Service Layer
   - Converte in Task model
   ↓
8. API Layer
   - Serializza in JSON
   - Ritorna TaskResponse
   ↓
9. Client HTTP
   - Riceve 201 Created + task JSON
```

---

## 🎯 Mapping Responsabilità

### API Layer (`app/api/`)
- ✅ Gestione richieste HTTP
- ✅ Validazione input (Pydantic)
- ✅ Serializzazione output (JSON)
- ✅ Autenticazione JWT (dependencies)
- ✅ Middleware (CORS, errors)
- ❌ **NO** business logic
- ❌ **NO** query dirette

### Service Layer (`app/services/`)
- ✅ Orchestrazione operazioni
- ✅ Business rules
- ✅ Coordinamento tra repository
- ✅ Gestione errori business
- ❌ **NO** HTTP handling
- ❌ **NO** query SQL dirette

### Repository Layer (`app/repositories/`)
- ✅ Query SQL
- ✅ Transazioni database
- ✅ Applicazione RLS
- ✅ Mapping DB → Models
- ❌ **NO** business logic
- ❌ **NO** HTTP handling

### Core Layer (`app/core/`)
- ✅ Configurazione app
- ✅ Connessione database
- ✅ Security (JWT, hashing)
- ✅ Exceptions custom
- ❌ **NO** business logic

### Utils Layer (`app/utils/`)
- ✅ Funzioni riutilizzabili
- ✅ Decorators
- ✅ Logger
- ✅ Validators generici
- ❌ **NO** dipendenze da altri layer

---

## 📝 Convenzioni Naming

### File
- `<domain>_<layer>.py` → `user_repository.py`
- `<feature>_<layer>.py` → `auth_service.py`
- Layer singolare → `model/`, non `models/`

### Classi
- PascalCase → `UserRepository`, `AuthService`
- Suffisso layer → `*Service`, `*Repository`

### Funzioni
- snake_case → `create_user()`, `get_tasks()`
- Verbi chiari → `get_`, `create_`, `update_`, `delete_`

### Import
- Assoluti → `from app.services.auth_service import AuthService`
- Mai relativi → ❌ `from ..services import auth_service`

---

## 🔗 Dipendenze tra Layer

```
                 ┌─────────────┐
                 │   Client    │
                 └──────┬──────┘
                        │
                        ▼
         ┌──────────────────────────┐
         │      API Layer           │
         │  (routes, middleware)    │
         └──────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │   Services Layer         │
         │  (business logic)        │
         └──────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │  Repositories Layer      │
         │  (data access + RLS)     │
         └──────────┬───────────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │      Database            │
         │   (PostgreSQL + RLS)     │
         └──────────────────────────┘

    Dipendenze Orizzontali:
    
    ┌─────────┐     ┌──────────┐
    │ Schemas │ ←── │   API    │
    └─────────┘     └──────────┘
         ▲               ▲
         └───────┬───────┘
                 │
         ┌───────┴───────┐
         │   Services    │
         └───────┬───────┘
                 │
         ┌───────▼───────┐
         │     Models    │
         └───────────────┘

    Shared:
    
    ┌────────────────────────┐
    │     Core + Utils       │
    │ (usati da tutti i layer)│
    └────────────────────────┘
```

---

## 🎨 Principi Applicati

### 1. Separation of Concerns
Ogni layer ha una responsabilità specifica e ben definita.

### 2. Dependency Inversion
Layer superiori dipendono da astrazioni (es. BaseRepository).

### 3. Single Responsibility
Ogni file/classe ha un solo scopo.

### 4. DRY (Don't Repeat Yourself)
Codice condiviso in `utils/` e `base_repository.py`.

### 5. Open/Closed Principle
Estendibile senza modificare codice esistente.

---

## 🚀 Scalabilità

### Aggiungere un Nuovo Dominio

Per aggiungere "Projects":

```
1. app/models/project.py           # Domain model
2. app/schemas/project.py          # DTO Pydantic
3. app/repositories/project_repository.py  # Data access
4. app/services/project_service.py # Business logic
5. app/api/routes/projects.py      # REST endpoints
6. main.py                          # Include router
7. tests/integration/test_project_crud.py  # Tests
8. docs/api/projects.md            # Documentation
```

### Aggiungere Feature a Dominio Esistente

Per aggiungere "search tasks":

```
1. app/repositories/task_repository.py
   → Aggiungi search_tasks(query)
   
2. app/services/task_service.py
   → Aggiungi search_tasks_service()
   
3. app/api/routes/tasks.py
   → Aggiungi GET /tasks/search?q=...
   
4. tests/integration/test_task_crud.py
   → Aggiungi test_search_tasks()
   
5. docs/api/authentication.md
   → Documenta nuovo endpoint
```

---

## 📚 File da Consultare

### Per iniziare
1. `README.md` - Overview progetto
2. `QUICK_START.md` - Setup rapido
3. `docs/development/setup.md` - Setup dettagliato

### Per sviluppare
1. `docs/architecture/layers.md` - Layer pattern
2. `docs/development/contributing.md` - Guidelines
3. `ARCHITECTURE_MIGRATION.md` - Storia e decisioni

### Per API
1. `docs/api/authentication.md` - Endpoint auth
2. http://localhost:8000/docs - Swagger UI
3. `app/api/routes/*.py` - Codice endpoint

---

**Struttura pulita, organizzata e scalabile! 🎯🇮🇹**

