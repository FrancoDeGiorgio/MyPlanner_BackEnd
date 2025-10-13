# My Planner – Backend API

Backend FastAPI per **My Planner**, piattaforma multi-tenant di gestione delle attività. Espone API REST protette con JWT, applica Row-Level Security su PostgreSQL/Supabase e gestisce i flussi di autenticazione e CRUD delle task con campi avanzati (titolo, colore, durata/data fine).

---

## 🚀 Stack Tecnologico

| Tecnologia / Modulo | Ruolo |
| --- | --- |
| FastAPI | Framework web asincrono (routing, dependency injection, OpenAPI) |
| PostgreSQL | Persistenza dati con Row-Level Security |
| psycopg2-binary | Driver PostgreSQL con gestione manuale delle transazioni |
| Pydantic v2 | Validazione input/output (`schemas.py`) |
| python-jose[cryptography] | Firma e verifica JWT (algoritmo HMAC) |
| passlib[bcrypt] | Hashing password sicuro |
| python-dotenv | Caricamento configurazione da variabili ambiente |
| python-multipart | Gestione form data per OAuth2 password flow |

---

## 🗂️ Struttura Progetto


```
MyPlanner_BackEnd/
├── main.py # Entrypoint FastAPI, include router auth/tasks
├── config.py # Config applicativa (lettura env, costanti)
├── database.py # Connessione Postgres, helper execute_protected_query
├── dependencies.py # Dipendenze condivise (es. get_current_user)
├── security.py # Hash password, verifica, creazione JWT
├── schemas.py # Modelli Pydantic per User, Token, Task
├── routers/
│ ├── auth.py # /auth/register, /auth/login
│ └── tasks.py # /tasks CRUD con enforcement RLS
├── requirements.txt # Dipendenze Python
├── runtime.txt # Versione Python per il deploy (es. Render)
└── README.md # Questo file
```

---


---

## 🔐 Sicurezza & Multi-Tenant

- **JWT**: il claim `sub` contiene `name_user`, utilizzato per impostare la variabile di contesto RLS `request.jwt.claim.sub` lato database.
- **Row-Level Security**: tutte le query sulle task passano da `execute_protected_query()` che:
  1. Imposta il ruolo `authenticated` per attivare le policy RLS.
  2. Imposta `request.jwt.claim.sub` con l'username autenticato.
  3. Esegue la query entro una transazione, rispettando le policy RLS.
- **Password hashing**: Bcrypt tramite Passlib (versione 1.7.4 + bcrypt 4.0.1).
- **Gestione errori**: rollback automatico su eccezioni, risposta HTTP coerente con FastAPI.
- **CORS**: configurato per permettere richieste da frontend locale (localhost:3000) e deploy Vercel.

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
   # Esempio per Supabase con PgBouncer
   DATABASE_URL=postgresql://postgres.xxxxx:password@aws-0-region.pooler.supabase.com:6543/postgres
   
   # Chiave segreta per JWT (generare una stringa casuale sicura)
   SECRET_KEY=super-secret-key-change-me-in-production
   
   # Durata token (in minuti)
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Algoritmo JWT
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

### Tabella `tasks` (Schema Finale)

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

**Note sulla migrazione:**
- Se stai aggiornando da una versione precedente, esegui le ALTER TABLE presenti in `script_sql.sql`.
- `end_time` e `duration_minutes` sono mutuamente esclusivi (validato lato backend in `schemas.TaskBase`).
- Il campo `color` accetta solo valori: `green`, `purple`, `orange`, `cyan`, `pink`, `yellow`.

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

La funzione `get_current_tenant_id()` risolve l'UUID partendo dal claim `sub` (vedi `MyPlanner_DB/policy RLS.sql`).

---

## 🌐 Configurazione CORS

Il backend è configurato per accettare richieste da:
- `http://localhost:3000` (sviluppo locale frontend)
- `https://*.vercel.app` (deploy frontend su Vercel)
- Temporaneamente: `*` (qualsiasi origine - da restringere in produzione)

Sono abilitati:
- **Credentials**: per gestire cookie/auth header
- **Tutti i metodi HTTP**: GET, POST, PUT, DELETE, OPTIONS
- **Tutti gli header**: incluso `Authorization` per JWT

**⚠️ Produzione**: rimuovere `"*"` da `allow_origins` e specificare solo i domini effettivi.

---

## 📡 Endpoints Principali

| Metodo | Path | Descrizione |
| --- | --- | --- |
| POST | `/auth/register` | Registra un nuovo utente (hash password) |
| POST | `/auth/login` | OAuth2 password flow → restituisce JWT |
| GET | `/tasks` | Lista task del tenant corrente (RLS enforced) |
| POST | `/tasks` | Crea una task con titolo, colore, durata/fine |
| PUT | `/tasks/{id}` | Aggiorna titolo/descrizione/colore/tempo/stato |
| DELETE | `/tasks/{id}` | Elimina una task del tenant |

I payload sono validati dai modelli Pydantic; errori producono HTTP status coerenti (400, 401, 404, 500).

---

## 🧠 Modelli Pydantic (estratto)

```python
ColorLiteral = Literal["green", "purple", "orange", "cyan", "pink", "yellow"]

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=1, max_length=255)
    color: ColorLiteral = Field(default="green")
    date_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=1440)
    completed: bool = False

    @model_validator(mode="after")
    def check_time_constraints(self):
        if self.end_time and self.duration_minutes:
            raise ValueError("Puoi impostare solo end_time oppure duration_minutes, non entrambi.")
        if self.end_time and self.end_time <= self.date_time:
            raise ValueError("La data di fine deve essere successiva alla data di inizio.")
        return self
```

**Note:**
- `TaskCreate` eredita da `TaskBase` (nessun `tenant_id` in input).
- `Task` aggiunge `id`, `tenant_id`, `created_at` per le risposte API.
- La validazione dell'esclusività `end_time`/`duration_minutes` è **solo lato backend** (non c'è constraint DB).

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
  
  U->>API: POST /tasks (Bearer token, task data)
  API->>API: Verifica JWT, estrae username
  API->>DB: SET role authenticated, SET request.jwt.claim.sub 
  API->>DB: INSERT INTO tasks (tenant_id, title, description, color, ...)
  DB-->>API: Task creata (con RLS check)
  API-->>U: Task object (201 Created)
```

---

## ✅ Testing & Debug

- **Swagger UI**: prova tutti gli endpoint con payload completi
  1. Registra utente: POST `/auth/register`
  2. Login: POST `/auth/login` (copia il token)
  3. Autorizza: clicca "Authorize" e incolla `Bearer <token>`
  4. Crea task: POST `/tasks` con tutti i campi

- **Test RLS diretto con psql**:
  ```sql
  -- Simula contesto autenticato
  SET role authenticated;
  SELECT set_config('request.jwt.claim.sub', 'utente_demo', true);
  
  -- Verifica visibilità task
  SELECT * FROM tasks;
  ```

- **Logging**: `execute_protected_query` stampa errori durante sviluppo. Controlla console per errori di mapping.

---

## 🚀 Deploy

### Render / Railway / Deta

1. **Variabili ambiente richieste**:
   - `DATABASE_URL` (con SSL e parametri PgBouncer se usi Supabase)
   - `SECRET_KEY` (stringa casuale sicura)
   - `ACCESS_TOKEN_EXPIRE_MINUTES` (opzionale, default 30)

2. **Start command**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

3. **Runtime**: `runtime.txt` specifica Python 3.11.x

### Supabase / Postgres Gestito

1. Esegui `MyPlanner_DB/script_sql.sql` per creare tabelle
2. Esegui `MyPlanner_DB/policy RLS.sql` per configurare RLS e funzione `get_current_tenant_id()`
3. Abilita SSL nella stringa di connessione
4. Per PgBouncer (porta 6543): il codice gestisce automaticamente `options: '-c pool_timeout=0'`

---

## 🛠️ Troubleshooting

### Errore: "Database operation failed"
- **Causa**: Connessione DB fallita o policy RLS non configurate.
- **Soluzione**: 
  - Verifica `DATABASE_URL` nelle variabili ambiente
  - Controlla che `get_current_tenant_id()` esista nel DB
  - Verifica che le policy RLS siano abilitate

### Errore: "SASL authentication failed"
- **Causa**: PgBouncer di Supabase richiede parametri speciali.
- **Soluzione**: Il codice in `database.py` gestisce automaticamente `options: '-c pool_timeout=0'`. Se persiste, verifica le credenziali.

### Task non visibili dopo creazione
- **Causa**: `tenant_id` non corrisponde all'utente autenticato.
- **Soluzione**: 
  - Verifica che il JWT contenga il `sub` corretto
  - Testa con psql impostando manualmente il contesto RLS

### Errore 401 su endpoint protetti
- **Causa**: Token JWT mancante, scaduto o invalido.
- **Soluzione**:
  - Rifai login per ottenere nuovo token
  - Verifica che `SECRET_KEY` sia coerente tra creazione e verifica token
  - Controlla che l'header sia `Authorization: Bearer <token>`

### Retry connessione DB
Il codice ritenta la connessione fino a 5 volte con delay di 2 secondi. Se fallisce:
- Verifica firewall/network
- Controlla che il servizio DB sia attivo
- Verifica SSL/TLS requirement

---

## 📋 Roadmap

- [ ] Endpoint aggregazioni (statistiche per giorno/settimana/mese)
- [ ] Test automatici con pytest (fixtures DB, test RLS)
- [ ] Rate limiting per `/auth/login` (prevenzione brute force)
- [ ] WebSocket/SSE per aggiornamenti realtime task
- [ ] Endpoint PATCH per aggiornamenti parziali
- [ ] Soft delete (campo `deleted_at` invece di DELETE)
- [ ] Paginazione per GET `/tasks` (quando molte task)

---

## 📦 Dipendenze Complete

```txt
fastapi
pydantic
uvicorn
psycopg2-binary
python-jose[cryptography]
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
python-dotenv
python-multipart
pydantic[email]
```

---

## 📄 Licenza

Parte della suite **My Planner** – distribuito con licenza MIT. Contributi e segnalazioni sono benvenuti!

---

## 🤝 Contribuire

1. Fork del repository
2. Crea branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

Per bug o feature request, apri un'issue su GitHub.