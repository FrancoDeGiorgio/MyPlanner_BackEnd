# My Planner – Backend API

Backend FastAPI per **My Planner**, piattaforma multi-tenant di gestione delle attività. Espone API REST protette con JWT, applica Row-Level Security su PostgreSQL/Supabase e gestisce i flussi di autenticazione e CRUD delle task con campi avanzati (titolo, colore, durata/data fine).

---

## 🚀 Stack Tecnologico

| Tecnologia / Modulo | Ruolo |
| --- | --- |
| FastAPI | Framework web asincrono (routing, dependency injection, OpenAPI) |
| PostgreSQL | Persistenza dati con Row-Level Security |
| psycopg2 | Driver PostgreSQL con gestione manuale delle transazioni |
| Pydantic v1 | Validazione input/output (`schemas.py`) |
| python-jose | Firma e verifica JWT (algoritmo HMAC) |
| passlib[bcrypt] | Hashing password sicuro |
| python-dotenv | Caricamento configurazione da variabili ambiente |

---

## 🗂️ Struttura Progetto

```
MyPlanner_BackEnd/
├── main.py                # Entrypoint FastAPI, include router auth/tasks
├── config.py              # Config applicativa (lettura env, costanti)
├── database.py            # Connessione Postgres, helper execute_protected_query
├── dependencies.py        # Dipendenze condivise (es. get_current_user)
├── security.py            # Hash password, verifica, creazione JWT
├── schemas.py             # Modelli Pydantic per User, Token, Task
├── routers/
│   ├── auth.py            # /auth/register, /auth/login
│   └── tasks.py           # /tasks CRUD con enforcement RLS
├── requirements.txt       # Dipendenze Python
├── runtime.txt            # Versione Python per il deploy (es. Render)
└── README.md              # Questo file
```

---

## 🔐 Sicurezza & Multi-Tenant

- **JWT**: il claim `sub` contiene `name_user`, utilizzato per impostare la variabile di contesto RLS `request.jwt.claim.sub` lato database.
- **Row-Level Security**: tutte le query sulle task passano da `execute_protected_query()` che:
  1. Imposta `request.jwt.claim.sub` con l'username autenticato.
  2. Esegue la query entro una transazione, rispettando le policy RLS.
- **Password hashing**: Bcrypt tramite Passlib.
- **Gestione errori**: rollback automatico su eccezioni, risposta HTTP coerente con FastAPI.

---

## 📦 Setup Locale

1. **Ambiente virtuale**
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Windows: .venv\Scripts\activate
   ```

2. **Installazione dipendenze**
   ```bash
   pip install -r requirements.txt
   ```

3. **Variabili d'ambiente** (`.env` esempio)
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/myplanner
   SECRET_KEY=super-secret-key
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ALGORITHM=HS256
   ```

4. **Avvio server sviluppo**
   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. **Documentazione API**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

---

## 🧩 Schema Dati & Migrazioni

### Tabella `users`

```sql
CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name_user TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabella `tasks`

```sql
CREATE TABLE tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES users(id),
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    color VARCHAR(20) NOT NULL DEFAULT 'green',
    date_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NULL,
    duration_minutes INTEGER NULL CHECK (duration_minutes BETWEEN 5 AND 1440),
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

- `end_time` e `duration_minutes` sono mutuamente esclusivi (validato in `schemas.TaskBase`).
- Migrazioni consigliate: popolamento colonne, rimozione default `title` dopo upgrade.

### Policy Row-Level Security

```sql
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenants can only read their own tasks"
  ON tasks FOR SELECT TO authenticated
  USING (tenant_id = get_current_tenant_id());

CREATE POLICY "Tenants can insert their own tasks"
  ON tasks FOR INSERT TO authenticated
  WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY "Tenants can update their own tasks"
  ON tasks FOR UPDATE TO authenticated
  USING (tenant_id = get_current_tenant_id())
  WITH CHECK (tenant_id = get_current_tenant_id());

CREATE POLICY "Tenants can delete their own tasks"
  ON tasks FOR DELETE TO authenticated
  USING (tenant_id = get_current_tenant_id());
```

La funzione `get_current_tenant_id()` risolve l'UUID partendo dal claim `sub`.

---

## 📡 Endpoints Principali

| Metodo | Path | Descrizione |
| --- | --- | --- |
| POST | `/auth/register` | Registra un nuovo utente (hash password) |
| POST | `/auth/login` | OAuth2 password flow → restituisce JWT |
| GET | `/tasks` | Lista task del tenant corrente (RLS enforced) |
| POST | `/tasks` | Crea una task con i nuovi campi estesi |
| PUT | `/tasks/{id}` | Aggiorna titolo/descrizione/colore/tempo/stato |
| DELETE | `/tasks/{id}` | Elimina una task del tenant |

I payload sono validati dai modelli Pydantic; errori producono HTTP status coerenti.

---

## 🧠 Modelli Pydantic (estratto)

```python
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=1, max_length=255)
    color: Literal["green", "purple", "orange", "cyan", "pink", "yellow"] = "green"
    date_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=1440)
    completed: bool = False

    @model_validator(mode="after")
    def check_time_constraints(self):
        if self.end_time and self.duration_minutes:
            raise ValueError("Puoi impostare solo end_time oppure duration_minutes")
        if self.end_time and self.end_time <= self.date_time:
            raise ValueError("La data di fine deve essere successiva alla data di inizio")
        return self
```

`TaskCreate` eredita da `TaskBase`, mentre `Task` aggiunge `id`, `tenant_id`, `created_at`.

---

## 🔄 Flusso Autenticazione & Task

```mermaid
sequenceDiagram
  participant U as Utente
  participant API as FastAPI
  participant DB as PostgreSQL (RLS)

  U->>API: POST /auth/login (username, password)
  API->>DB: SELECT hashed_password FROM users WHERE name_user
  DB-->>API: hashed_password
  API-->>U: JWT (access_token, token_type)
  U->>API: GET /tasks (Authorization: Bearer)
  API->>DB: SET request.jwt.claim.sub = username
  DB-->>API: Task filtrate per tenant_id
  API-->>U: Lista task
```

---

## ✅ Testing & Debug

- **Swagger UI**: prova tutti gli endpoint con payload completi (titolo, colore, durata).
- **psql**: forza il contesto RLS e verifica visibilità dati
  ```sql
  SET LOCAL request.jwt.claim.sub = 'utente_demo';
  SELECT * FROM tasks;
  ```
- **Logging**: `execute_protected_query` stampa errori di mapping durante lo sviluppo.

---

## 🚀 Deploy

- **Render / Railway / Deta**
  - Impostare variabili ambiente (`DATABASE_URL`, `SECRET_KEY`, ecc.).
  - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
  - `runtime.txt` indica la versione Python (`python-3.11.x`).
- **Supabase / Postgres gestito**
  - Eseguire `MyPlanner_DB/script_sql.sql` + `policy RLS.sql`.
  - Configurare funzione `get_current_tenant_id`.

---

## 📋 Roadmap

- Endpoint aggregazioni (statistiche per giorno/settimana).
- Test automatici (pytest + database temporaneo / fixtures).
- Rate limiting per `/auth/login`.
- Eventuale supporto WebSocket/SSE per aggiornamenti realtime.

---

## 📄 Licenza

Parte della suite **My Planner** – distribuito con licenza MIT. Contributi e segnalazioni sono benvenuti!
