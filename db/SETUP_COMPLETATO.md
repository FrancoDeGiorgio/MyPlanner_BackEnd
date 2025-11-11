# ✅ Setup Database Aggiornato

Questa nota riepiloga lo stato attuale dopo l'allineamento della pipeline database.

---

## 📁 Struttura Cartella `db/`

```
MyPlanner_BackEnd/db/
├── 00_extensions.sql   # Estensioni richieste (pgcrypto)
├── init.sql            # Seeds opzionali, vuoto per default
├── README.md           # Guida completa
├── TEST_DB.md          # Procedure di verifica
└── SETUP_COMPLETATO.md # Questo file
```

---

## 🚀 Flusso di Avvio Aggiornato

1. `docker compose up --build`
2. Il container `db` esegue automaticamente gli script in `db/` (estensioni + seed)
3. Il container backend esegue `alembic upgrade head`
4. L'applicazione parte con schema e dati allineati

> Alembic è ora l'unica fonte di verità per lo schema. `init.sql` resta a disposizione solo per eventuali dati seed.

---

## 🔄 Reset Ambiente

Per ricreare da zero il database:

```bash
docker compose down -v
docker compose up --build
```

---

## 🛠️ Modifica Schema

1. Genera una migrazione: `alembic revision --autogenerate -m "descrizione"`
2. Controlla/affina il file generato
3. Applica: `alembic upgrade head`

Se colleghi un database legacy (già popolato), valuta:

```bash
alembic stamp 001  # riconosce lo schema iniziale
alembic upgrade head
```

Oppure ricrea il volume (`docker compose down -v`).

---

## 🧪 Verifica Rapida

```powershell
# Registrazione
Invoke-RestMethod -Uri "http://localhost:8000/auth/register" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name_user":"testuser","password":"Test123!"}'

# Login
$token = (Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
  -Body "username=testuser&password=Test123!").access_token

# Creazione task
Invoke-RestMethod -Uri "http://localhost:8000/tasks" `
  -Method POST `
  -Headers @{"Authorization"="Bearer $token";"Content-Type"="application/json"} `
  -Body '{"title":"Prima Task","description":"Test pipeline","color":"green","date_time":"2025-11-10T10:00:00","duration_minutes":30,"completed":false}'
```

---

## ⚠️ Troubleshooting

- **Errore `relation already exists` all'avvio**
  - Opzione A: `docker compose down -v && docker compose up --build`
  - Opzione B: impostare `ALEMBIC_STAMP_LEGACY_SCHEMA=1` o eseguire manualmente `alembic stamp 001`

- **Seed non eseguiti**
  - Ricordati che `init.sql` gira solo su volume vuoto. Usa `docker compose down -v`.

---

## 📌 Stato

- Docker Compose allinea automaticamente estensioni e variabili
- Alembic gestisce l'intero schema (incluso `pgcrypto`)
- Documentazione aggiornata (`README.md`, `SETUP_COMPLETATO.md`)

**Ultimo aggiornamento**: 2025-11-11  
**Responsabile**: Team MyPlanner  
**Stato**: ✅ Allineato alla nuova pipeline Alembic

