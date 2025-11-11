# 🧪 Test Database Setup

Guida rapida per verificare che il database sia stato inizializzato correttamente.

---

## ✅ Test 1: Verifica Inizializzazione Automatica

```bash
# 1. Reset completo (rimuove tutto)
cd C:\Users\Utente\Desktop\MyPlanner
docker-compose down -v

# 2. Avvia container (init.sql viene eseguito automaticamente)
docker-compose up -d

# 3. Aspetta che il DB sia healthy (5-10 secondi)
docker-compose ps

# 4. Verifica log inizializzazione
docker-compose logs db | Select-String -Pattern "INIZIALIZZATO"
```

**Output atteso**:
```
NOTICE:  DATABASE MYPLANNER INIZIALIZZATO
NOTICE:  Tabelle create: users, tasks
NOTICE:  Ruoli creati: authenticated
```

---

## ✅ Test 2: Verifica Tabelle

```bash
# Connettiti al database
docker-compose exec db psql -U myplanner -d myplanner

# Lista tabelle (dovresti vedere users e tasks)
\dt

# Dettaglio tabella users
\d users

# Dettaglio tabella tasks
\d tasks

# Esci
\q
```

**Output atteso**:
```
         List of relations
 Schema | Name  | Type  |   Owner   
--------+-------+-------+-----------
 public | tasks | table | myplanner
 public | users | table | myplanner
```

---

## ✅ Test 3: Verifica Indici

```bash
docker-compose exec db psql -U myplanner -d myplanner -c "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' ORDER BY indexname;"
```

**Output atteso**:
```
          indexname          
-----------------------------
 idx_tasks_completed
 idx_tasks_date_time
 idx_tasks_tenant_date
 idx_tasks_tenant_id
 tasks_pkey
 users_pkey
 users_name_user_key
```

---

## ✅ Test 4: Verifica Trigger

```bash
docker-compose exec db psql -U myplanner -d myplanner -c "SELECT trigger_name FROM information_schema.triggers WHERE event_object_table = 'tasks';"
```

**Output atteso**:
```
      trigger_name       
-------------------------
 update_tasks_updated_at
```

---

## ✅ Test 5: Test Funzionale Completo

### 5.1 Registrazione Utente

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/auth/register" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"name_user":"testdb","password":"TestDB123!"}'
```

**Output atteso**: `201 Created` con `user_id`

### 5.2 Login

```powershell
$token = (Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
  -Method POST `
  -Headers @{"Content-Type"="application/x-www-form-urlencoded"} `
  -Body "username=testdb&password=TestDB123!").access_token

Write-Host "Token: $token"
```

**Output atteso**: Token JWT

### 5.3 Crea Task

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/tasks" `
  -Method POST `
  -Headers @{"Authorization"="Bearer $token";"Content-Type"="application/json"} `
  -Body '{"title":"Test DB Task","description":"Testing database init","color":"green","date_time":"2025-11-10T10:00:00","duration_minutes":30,"completed":false}'
```

**Output atteso**: `201 Created` con task completa

### 5.4 Recupera Task

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/tasks" `
  -Method GET `
  -Headers @{"Authorization"="Bearer $token"}
```

**Output atteso**: Array con la task creata

---

## ✅ Test 6: Verifica Dati nel Database

```bash
# Utente creato
docker-compose exec db psql -U myplanner -d myplanner -c "SELECT id, name_user, created_at FROM users WHERE name_user = 'testdb';"

# Task creata
docker-compose exec db psql -U myplanner -d myplanner -c "SELECT id, title, description, color, date_time FROM tasks WHERE title = 'Test DB Task';"
```

---

## ✅ Test 7: Verifica Trigger updated_at

```bash
# 1. Crea una task e annota l'ID
docker-compose exec db psql -U myplanner -d myplanner -c "SELECT id, created_at, updated_at FROM tasks LIMIT 1;"

# 2. Aggiorna la task
docker-compose exec db psql -U myplanner -d myplanner -c "UPDATE tasks SET title = 'Updated Title' WHERE id = '<task-id>';"

# 3. Verifica che updated_at sia cambiato
docker-compose exec db psql -U myplanner -d myplanner -c "SELECT id, created_at, updated_at FROM tasks WHERE id = '<task-id>';"
```

**Output atteso**: `updated_at` > `created_at`

---

## 🔄 Reset e Reinizializza

Se modifichi `init.sql` e vuoi riapplicarlo:

```bash
# 1. Ferma tutto e rimuovi volumi
docker-compose down -v

# 2. Verifica rimozione volume
docker volume ls | Select-String "myplanner"

# 3. Riavvia (init.sql verrà rieseguito)
docker-compose up -d

# 4. Verifica log
docker-compose logs db --tail 50
```

---

## 🐛 Troubleshooting

### Problema: Tabelle non create

```bash
# Verifica che init.sql sia montato
docker-compose exec db ls -la /docker-entrypoint-initdb.d/

# Output atteso: init.sql deve essere presente
```

### Problema: Script non eseguito

Lo script viene eseguito **solo se il volume è vuoto**:

```bash
# Soluzione: rimuovi volume
docker-compose down -v
docker-compose up -d
```

### Problema: Errori SQL nello script

```bash
# Controlla log dettagliati
docker-compose logs db | Select-String -Pattern "ERROR|FATAL"
```

---

## 📊 Query Utili

### Conta record

```sql
SELECT 'users' AS table_name, COUNT(*) FROM users
UNION ALL
SELECT 'tasks' AS table_name, COUNT(*) FROM tasks;
```

### Dimensione database

```sql
SELECT 
    pg_size_pretty(pg_database_size('myplanner')) AS db_size;
```

### Attività per utente

```sql
SELECT 
    u.name_user,
    COUNT(t.id) AS num_tasks,
    SUM(CASE WHEN t.completed THEN 1 ELSE 0 END) AS completed_tasks
FROM users u
LEFT JOIN tasks t ON u.id = t.tenant_id
GROUP BY u.name_user
ORDER BY num_tasks DESC;
```

---

## ✅ Checklist Completa

- [ ] Database container avviato
- [ ] Script init.sql eseguito (vedi log)
- [ ] Tabelle `users` e `tasks` create
- [ ] Indici creati (4 indici su tasks)
- [ ] Trigger `update_tasks_updated_at` attivo
- [ ] Ruolo `authenticated` creato
- [ ] Permessi configurati
- [ ] API registrazione funziona
- [ ] API login funziona
- [ ] API task CRUD funziona
- [ ] Dati persistono dopo restart

**Se tutti i test passano: Database pronto! ✅🎉**

