# 🗄️ Database Setup - MyPlanner

Questa cartella contiene tutto il necessario per inizializzare il database PostgreSQL.

---

## 📁 Struttura

```
db/
├── 00_extensions.sql  # Estensioni richieste al bootstrap
├── init.sql           # Seed opzionali (vuoto per default)
├── README.md          # Questa guida
└── SETUP_COMPLETATO.md (stato setup)
```

---

## 🚀 Come Funziona

### Inizializzazione Automatica

Quando avvii Docker Compose per la **prima volta**:

1. PostgreSQL esegue in ordine alfabetico gli script nella cartella `db/`
   - `00_extensions.sql` abilita le estensioni obbligatorie (es. `pgcrypto`)
   - `init.sql` è disponibile per eventuali dati seed (vuoto di default)
2. Il container backend, tramite `entrypoint.sh`, lancia `alembic upgrade head`
3. Alembic crea l'intero schema (tabelle, indici, trigger, permessi)

> Non è più necessario mantenere manualmente lo schema dentro `init.sql`: le migrazioni sono l'unica fonte di verità. 🎉

---

## 🔄 Reset Database

Se vuoi resettare completamente il database:

```bash
# 1. Ferma e rimuovi tutto (inclusi volumi)
docker compose down -v

# 2. Riavvia (init.sql verrà rieseguito)
docker compose up -d
```

---

## 🛠️ Modifica Schema

### Workflow consigliato (Alembic)

1. Genera una nuova migrazione:
   ```bash
   alembic revision --autogenerate -m "descrizione"
   ```
2. Verifica e, se necessario, correggi il file generato in `app/migrations/versions/`
3. Applica la migrazione:
   ```bash
   alembic upgrade head
   ```

### Dati seed opzionali

- Inserisci record di test in `init.sql` (solo quando il volume è vuoto)
- Per rieseguire i seed: `docker compose down -v && docker compose up -d`

### Database legacy già popolati

Se colleghi un database creato prima di Alembic e incontri errori tipo `relation already exists`, scegli una delle due strade:

```bash
# Opzione 1: reset completo
docker compose down -v
docker compose up --build

# Opzione 2: allinea lo stato delle migrazioni
alembic stamp 001
alembic upgrade head
```

---

## 📊 Schema Database

### Tabella: `users`

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| `id` | UUID | PK, tenant_id per RLS |
| `name_user` | VARCHAR(50) | Username univoco |
| `hashed_password` | TEXT | Password bcrypt |
| `created_at` | TIMESTAMP | Data registrazione |

### Tabella: `tasks`

| Colonna | Tipo | Descrizione |
|---------|------|-------------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK → users(id) |
| `title` | VARCHAR(200) | Titolo task |
| `description` | TEXT | Descrizione |
| `color` | VARCHAR(20) | Colore (green, purple, etc) |
| `date_time` | TIMESTAMP | Data/ora inizio |
| `end_time` | TIMESTAMP | Data/ora fine (opzionale) |
| `duration_minutes` | INTEGER | Durata minuti (opzionale) |
| `completed` | BOOLEAN | Flag completamento |
| `created_at` | TIMESTAMP | Data creazione |
| `updated_at` | TIMESTAMP | Data ultimo aggiornamento |

**Vincoli**:
- `duration_minutes >= 5` (se specificato)
- `end_time > date_time` (se specificato)
- `end_time` e `duration_minutes` mutualmente esclusivi (validato a livello applicazione)

---

## 🔐 Row-Level Security (RLS)

### Locale (Docker)
- **DISABILITATO** per semplicità sviluppo
- Multi-tenancy gestito a livello applicazione

### Produzione (Supabase)
- **ABILITATO** per sicurezza
- Policy: `tenant_id = current_setting('jwt.claims.user_id')::uuid`

Per abilitare RLS in locale (testing):

```sql
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON tasks
    FOR ALL
    USING (tenant_id = current_setting('jwt.claims.user_id')::uuid);
```

---

## 🧪 Testing

### Connessione Manuale

```bash
# Connettiti al database
docker-compose exec db psql -U myplanner -d myplanner

# Query di esempio
SELECT * FROM users;
SELECT * FROM tasks;

# Info schema
\dt          # Lista tabelle
\d users     # Dettaglio tabella users
\d tasks     # Dettaglio tabella tasks
```

### Verifica Inizializzazione

```sql
-- Controlla tabelle
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- Controlla indici
SELECT indexname FROM pg_indexes 
WHERE schemaname = 'public';

-- Controlla trigger
SELECT trigger_name FROM information_schema.triggers 
WHERE event_object_table = 'tasks';
```

---

## 📝 Note

### Dati di Test

Per inserire dati di test, decommenta la sezione **7. DATI DI TEST** in `init.sql`:

```sql
INSERT INTO users (name_user, hashed_password) VALUES
('testuser', '$2b$12$...')  -- password: testpass123
ON CONFLICT (name_user) DO NOTHING;
```

### Backup

```bash
# Backup database
docker-compose exec db pg_dump -U myplanner myplanner > backup.sql

# Restore
docker-compose exec -T db psql -U myplanner myplanner < backup.sql
```

---

## 🆘 Troubleshooting

### Errore: "relation already exists"

```bash
docker compose down -v
docker compose up --build
```

Oppure, se lo schema esistente è già allineato alla revisione iniziale:

```bash
alembic stamp 001
alembic upgrade head
```

### init.sql non viene eseguito

Il file `init.sql` viene eseguito **solo alla prima creazione** del volume.

**Soluzione**: Rimuovi il volume:
```bash
docker compose down -v
docker volume rm myplanner_db_data
docker compose up -d
```

### Modifiche a init.sql non applicate

Devi **rimuovere il volume** per rieseguire lo script:
```bash
docker compose down -v
docker compose up -d
```

---

## 🔗 Link Utili

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Docker PostgreSQL Image](https://hub.docker.com/_/postgres)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)

---

**Database pronto per lo sviluppo! 🚀**

