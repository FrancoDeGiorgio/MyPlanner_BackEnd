# Migrazione a SQLAlchemy ORM + Alembic - Completata ✅

## Sommario

La migrazione da psycopg2 raw SQL a SQLAlchemy ORM con Alembic per la gestione delle migrazioni è stata completata con successo. Il sistema preserva tutti i dati esistenti e mantiene la funzionalità Row-Level Security (RLS) tramite event listeners.

## Modifiche Implementate

### 1. Dipendenze e Configurazione

**File modificati:**
- `requirements.txt`: Aggiunti `sqlalchemy>=2.0`, `alembic`, `greenlet`
- `app/core/config.py`: Già esistente, nessuna modifica necessaria
- `app/core/database.py`: Refactoring completo per SQLAlchemy

**Novità in `database.py`:**
- `engine`: Motore SQLAlchemy per connessione PostgreSQL
- `SessionLocal`: Factory per creare sessioni database
- `Base`: Classe base per modelli ORM
- `get_db()`: Dependency injection per FastAPI (sostituisce `get_db_conn()`)
- Event listener automatico per configurare RLS prima di ogni query

### 2. Modelli ORM

**File convertiti:**
- `app/models/user.py`: Da dataclass a SQLAlchemy ORM model
- `app/models/task.py`: Da dataclass a SQLAlchemy ORM model con business logic
- `app/models/__init__.py`: Esporta `Base`, `User`, `Task`

**Caratteristiche dei modelli:**
- Mappatura diretta sulle tabelle PostgreSQL esistenti
- Relationships bidirezionali (User.tasks ↔ Task.owner)
- Metodi business logic mantenuti (`get_effective_duration`, `is_overdue`)
- Cascade delete: eliminando un User si eliminano automaticamente le sue Task

### 3. Sistema di Migrazioni Alembic

**File creati:**
- `alembic.ini`: Configurazione Alembic (nella root del progetto)
- `app/migrations/env.py`: Environment configuration con autogeneration
- `app/migrations/script.py.mako`: Template per nuove migrazioni
- `app/migrations/versions/001_initial_schema_from_existing_db.py`: Migrazione baseline

**Come usare Alembic:**

```bash
# Per database ESISTENTE (con dati da preservare):
cd MyPlanner_BackEnd
alembic stamp head  # Marca il DB come aggiornato SENZA eseguire migrazioni

# Per creare nuove migrazioni (es. aggiungere una colonna):
alembic revision --autogenerate -m "add_priority_column"

# Applicare migrazioni:
alembic upgrade head

# Rollback:
alembic downgrade -1

# Vedere lo storico:
alembic history

# Vedere lo stato corrente:
alembic current
```

### 4. Repository Layer

**File refactorati:**
- `app/repositories/user_repository.py`: Query SQLAlchemy ORM
- `app/repositories/task_repository.py`: Query SQLAlchemy ORM con RLS

**Principali cambiamenti:**
- `conn: psycopg2.connection` → `db: Session`
- Query raw SQL → Query ORM (`db.query(Task).filter()...`)
- Restituiscono oggetti ORM invece di dict
- RLS configurato tramite `set_rls_context(db, username)`
- Decorator `@with_rls_context` rimosso (sostituito da event listener)

### 5. Service Layer

**File refactorati:**
- `app/services/auth_service.py`: Usa `Session` e oggetti `User` ORM
- `app/services/task_service.py`: Usa `Session` e oggetti `Task` ORM

**Principali cambiamenti:**
- `conn: psycopg2.connection` → `db: Session`
- Nessuna conversione dict → Pydantic (ORM models si serializzano automaticamente)
- Accesso agli attributi: `user['name_user']` → `user.name_user`

### 6. API Routes

**File refactorati:**
- `app/api/routes/auth.py`: Usa `get_db` e `Session`
- `app/api/routes/tasks.py`: Usa `get_db` e `Session`

**Principali cambiamenti:**
- `Depends(get_db_conn)` → `Depends(get_db)`
- `conn: psycopg2.extensions.connection` → `db: Session`
- Passaggio parametri espliciti ai service methods

### 7. Codice Rimosso

**File eliminati:**
- `app/utils/decorators.py`: Il decorator `@with_rls_context` non è più necessario

**Funzioni rimosse da `database.py`:**
- `execute_protected_query()`: Sostituita da query ORM con event listener
- `get_user_id_by_username()`: Ora in `UserRepository`

## Funzionamento Row-Level Security (RLS)

### Come Funzionava Prima (psycopg2)
```python
@with_rls_context
def get_tasks(conn, username):
    # Il decorator configurava manualmente:
    # SET role authenticated;
    # set_config('request.jwt.claim.sub', username);
    cur.execute("SELECT * FROM tasks")
```

### Come Funziona Ora (SQLAlchemy)
```python
def get_tasks(db: Session, username: str):
    set_rls_context(db, username)  # Imposta username nella sessione
    # L'event listener in database.py configura automaticamente RLS
    # prima di OGNI query
    return db.query(Task).all()
```

**Event Listener in `database.py`:**
```python
@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    username = context.execution_options.get('username')
    if username:
        cursor.execute("SET role authenticated;")
        cursor.execute("SELECT set_config('request.jwt.claim.sub', %s, true)", (username,))
        cursor.execute("SELECT set_config('request.jwt.claim.role', 'authenticated', true)")
```

## Testing e Verifica

### Test Manuali Consigliati

1. **Test Autenticazione:**
   ```bash
   # Registrazione
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{"name_user": "test_user", "password": "testpass123"}'
   
   # Login
   curl -X POST http://localhost:8000/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test_user&password=testpass123"
   ```

2. **Test CRUD Tasks:**
   ```bash
   # Creare task (usa il token dal login)
   curl -X POST http://localhost:8000/tasks \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Test Task",
       "description": "Task di test",
       "color": "green",
       "date_time": "2025-12-01T10:00:00",
       "duration_minutes": 60,
       "completed": false
     }'
   
   # Leggere tasks
   curl -X GET http://localhost:8000/tasks \
     -H "Authorization: Bearer <token>"
   ```

3. **Test RLS (Isolamento Tenant):**
   - Creare 2 utenti diversi
   - Creare task per ciascuno
   - Verificare che user1 NON veda le task di user2

4. **Test Migrazioni Alembic:**
   ```bash
   # Creare una migrazione di test
   alembic revision --autogenerate -m "test_migration"
   
   # Applicare
   alembic upgrade head
   
   # Rollback
   alembic downgrade -1
   ```

### Test Automatici

Eseguire i test esistenti:
```bash
cd MyPlanner_BackEnd
pytest tests/integration/
```

## Vantaggi della Nuova Architettura

1. **Type Safety**: SQLAlchemy fornisce type hints migliori
2. **Meno SQL Manuale**: Query ORM sono più leggibili e manutenibili
3. **Autogenerazione Migrazioni**: Alembic rileva automaticamente i cambiamenti
4. **Gestione Relazioni**: Navigare tra User e Task è più semplice
5. **Testing**: Mock e fixture più facili con ORM
6. **Ecosistema**: Accesso a tutta la community SQLAlchemy

## Note Importanti

### Per Sviluppo Locale

1. **Prima di iniziare:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Se il database esiste già:**
   ```bash
   # NON eseguire alembic upgrade!
   # Invece marca il DB come aggiornato:
   alembic stamp head
   ```

3. **Per nuove modifiche allo schema:**
   ```bash
   # 1. Modifica i modelli ORM in app/models/
   # 2. Genera migrazione automatica:
   alembic revision --autogenerate -m "descrizione_modifica"
   # 3. Verifica il file generato in app/migrations/versions/
   # 4. Applica la migrazione:
   alembic upgrade head
   ```

### Per Produzione

1. **Prima del deploy:**
   - Verificare che tutte le migrazioni siano testate
   - Fare backup del database
   - Testare le migrazioni in staging

2. **Durante il deploy:**
   ```bash
   # Applicare le migrazioni
   alembic upgrade head
   
   # Verificare lo stato
   alembic current
   ```

3. **In caso di problemi:**
   ```bash
   # Rollback all'ultima versione funzionante
   alembic downgrade <revision_id>
   ```

## Troubleshooting

### Errore: "Can't locate revision identified by 'xxx'"
```bash
# Il database non è sincronizzato con Alembic
# Soluzione: Marca manualmente la versione corrente
alembic stamp head
```

### Errore: "Target database is not up to date"
```bash
# Applicare le migrazioni pending
alembic upgrade head
```

### Errore: "RLS not working / vedere task di altri utenti"
```bash
# Verificare che set_rls_context() sia chiamato nei repository
# Verificare che l'event listener sia attivo in database.py
# Verificare che le policy RLS siano abilitate in produzione
```

### Errore: "sqlalchemy.exc.OperationalError: could not connect"
```bash
# Verificare che DATABASE_URL sia impostata
echo $DATABASE_URL
# Verificare che PostgreSQL sia in esecuzione
# Verificare le credenziali di connessione
```

## Prossimi Passi Consigliati

1. **Eseguire test completi** per verificare che tutto funzioni
2. **Aggiornare la documentazione** API se necessario
3. **Configurare CI/CD** per eseguire migrazioni automaticamente
4. **Implementare monitoring** per tracciare performance query ORM
5. **Considerare index ottimizzati** basati su query patterns reali

## Conclusioni

La migrazione è stata completata con successo. Il sistema ora utilizza:
- ✅ SQLAlchemy ORM per type safety e produttività
- ✅ Alembic per versionamento e gestione migrazioni
- ✅ Event listeners per RLS automatico
- ✅ Relationships ORM per navigazione tra entità
- ✅ Preservazione dei dati esistenti

Il codice è più pulito, più sicuro e più manutenibile. 🎉

