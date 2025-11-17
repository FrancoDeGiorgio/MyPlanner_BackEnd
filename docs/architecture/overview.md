# Panoramica Architettura MyPlanner Backend

**Ultimo aggiornamento**: 2025-11-06

## 🏗️ Architettura a Layer

Il backend MyPlanner segue un'architettura a layer moderna che separa le responsabilità e migliora manutenibilità, testabilità e scalabilità.

## 📊 Diagramma Layer

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│    (app/api/routes, middleware)         │
│  - Gestione richieste HTTP              │
│  - Validazione input/output             │
│  - Serializzazione JSON                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Business Logic Layer              │
│          (app/services)                 │
│  - Orchestrazione operazioni            │
│  - Regole di business                   │
│  - Coordinamento tra layer              │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Data Access Layer                 │
│        (app/repositories)               │
│  - Query SQL                            │
│  - Gestione RLS                         │
│  - Transazioni database                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Database Layer                 │
│      PostgreSQL + Supabase RLS          │
│  - Persistenza dati                     │
│  - Row-Level Security                   │
│  - Isolamento multi-tenant              │
└─────────────────────────────────────────┘
```

## 🗂️ Struttura Directory

```
app/
├── api/                    # Presentation Layer
│   ├── routes/            # Endpoint REST
│   ├── middleware/        # CORS, error handling
│   └── dependencies.py    # Dependency injection
│
├── services/              # Business Logic Layer
│   ├── auth_service.py
│   └── task_service.py
│
├── repositories/          # Data Access Layer
│   ├── base_repository.py
│   ├── user_repository.py
│   └── task_repository.py
│
├── models/                # Domain Models
│   ├── user.py
│   └── task.py
│
├── schemas/               # DTO (Pydantic)
│   ├── auth.py
│   └── task.py
│
├── core/                  # Infrastruttura
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   └── exceptions.py
│
└── utils/                 # Utilities
    ├── decorators.py
    ├── logger.py
    └── validators.py
```

## 🔄 Flusso di una Richiesta

### Esempio: Creazione Task

1. **Client** → `POST /tasks` con JWT Bearer token
2. **Middleware CORS** → Valida origine richiesta
3. **Router** (`app/api/routes/tasks.py`) → Riceve richiesta
4. **Dependency** (`get_current_user`) → Estrae username da JWT
5. **Validation** (Pydantic) → Valida `TaskCreate` schema
6. **Service** (`TaskService.create_task`) → Business logic:
   - Recupera `tenant_id` da username
   - Valida che utente esista
   - Chiama repository
7. **Repository** (`TaskRepository.create_task`) → Data access:
   - Applica contesto RLS
   - Esegue INSERT con RETURNING
   - Commit transazione
8. **Service** → Mappa risultato in `Task` Pydantic
9. **Router** → Serializza in JSON e restituisce HTTP 201

## 🎯 Principi Chiave

### Separation of Concerns
Ogni layer ha una responsabilità specifica e non invade competenze degli altri layer.

### Dependency Inversion
I layer superiori dipendono da astrazioni, non da implementazioni concrete.

### Single Responsibility
Ogni classe/modulo ha un solo motivo per cambiare.

### DRY (Don't Repeat Yourself)
Codice condiviso è estratto in utilities o base classes.

## 🔐 Sicurezza

### Multi-Tenancy con RLS
- **Row-Level Security** a livello database
- Ogni utente è un tenant isolato
- Policy PostgreSQL garantiscono isolamento dati
- Context JWT configurato prima di ogni query

### Autenticazione JWT
- Token firmato con HS256
- Claim `sub` contiene username
- Scadenza configurabile (default 30 min)
- Password hashate con bcrypt

## 📈 Vantaggi Architettura

### Manutenibilità
- ✅ Modifiche localizzate per layer
- ✅ Refactoring sicuro
- ✅ Debug più semplice
- ✅ Code review focalizzate

### Testabilità
- ✅ Test unitari per layer
- ✅ Mock facili da creare
- ✅ Test isolati
- ✅ Coverage completa possibile

### Scalabilità
- ✅ Nuovi domini facilmente aggiungibili
- ✅ Servizi indipendenti
- ✅ Caching implementabile per layer
- ✅ Microservices migration possibile

## 🔗 Riferimenti

- [Layer Pattern Dettagliato](layers.md)
- [Implementazione RLS](rls_implementation.md)
- [ADR 001: Scelta Architettura](../adr/001-layered-architecture.md)

---

**Next**: Leggi [Layer Pattern](layers.md) per dettagli su ogni layer.

