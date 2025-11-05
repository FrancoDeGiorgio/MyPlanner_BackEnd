# ✅ Post-Refactoring Checklist

Questo documento contiene i passi da seguire per verificare e testare il backend refactorato.

---

## 🔍 Verifica Immediata

### 1. Verifica Struttura File
```bash
# Verifica che tutti i file siano presenti
ls -R domains/
ls -R core/
ls -R tests/
```

**Verifica visiva** (già fatto ✅):
- ✅ `domains/auth/` con 6 file (router, service, repository, models, schemas, __init__)
- ✅ `domains/tasks/` con 6 file (router, service, repository, models, schemas, __init__)
- ✅ `core/` con 3 file (decorators, dependencies, __init__)
- ✅ `tests/` con 4 file (conftest, test_auth, test_tasks, __init__)

### 2. Verifica Linter
```bash
# Nessun errore di linter (già verificato ✅)
# Se hai pylint/flake8 installato:
pylint main.py domains/ core/
flake8 main.py domains/ core/
```

### 3. Avvio Server
```bash
# Attiva ambiente virtuale (se presente)
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Installa dipendenze (se necessario)
pip install -r requirements.txt

# Avvia server
uvicorn main:app --reload --port 8000
```

**Verifica**:
- [ ] Server si avvia senza errori di import
- [ ] Nessun warning su import deprecati
- [ ] Console mostra endpoint registrati

---

## 🧪 Test Funzionali

### 1. Swagger UI
Apri browser su `http://localhost:8000/docs`

**Test Auth**:
- [ ] POST `/auth/register` visibile
- [ ] POST `/auth/login` visibile
- [ ] Prova registrazione con username e password
- [ ] Prova login e copia il token JWT
- [ ] Click "Authorize" e incolla `Bearer <token>`

**Test Tasks**:
- [ ] GET `/tasks` visibile e protetto (richiede auth)
- [ ] POST `/tasks` visibile e protetto
- [ ] PUT `/tasks/{task_id}` visibile e protetto
- [ ] DELETE `/tasks/{task_id}` visibile e protetto
- [ ] Prova creare una task (dopo aver fatto login)
- [ ] Verifica che la task venga restituita con ID e tenant_id
- [ ] Prova aggiornare la task
- [ ] Prova eliminare la task

### 2. Test RLS (Row-Level Security)

**Con psql o pgAdmin**:
```sql
-- Simula utente 1
SET role authenticated;
SELECT set_config('request.jwt.claim.sub', 'user1', true);
INSERT INTO tasks (tenant_id, title, description, color, date_time, completed)
VALUES (
    (SELECT id FROM users WHERE name_user = 'user1'),
    'Task User 1',
    'Descrizione',
    'green',
    NOW(),
    false
);

-- Simula utente 2
RESET role;
SET role authenticated;
SELECT set_config('request.jwt.claim.sub', 'user2', true);
SELECT * FROM tasks;  -- NON deve vedere la task di user1

-- Verifica che RLS funzioni
```

**Checklist**:
- [ ] User1 vede solo le proprie task
- [ ] User2 non vede task di User1
- [ ] User2 non può modificare task di User1
- [ ] User2 non può eliminare task di User1

---

## 📊 Verifica Architettura

### 1. Separazione Layer

**API Layer (Router)**:
```python
# Apri domains/tasks/router.py
# Verifica che:
```
- [ ] Non contenga query SQL dirette
- [ ] Non contenga business logic complessa
- [ ] Deleghi tutto al service
- [ ] Contenga solo validazione Pydantic e gestione HTTP

**Service Layer**:
```python
# Apri domains/tasks/service.py
# Verifica che:
```
- [ ] Non contenga query SQL dirette
- [ ] Coordini tra repository
- [ ] Contenga validazioni business (es. tenant_id valido)
- [ ] Mappi tra dict (repository) e Pydantic (API)

**Repository Layer**:
```python
# Apri domains/tasks/repository.py
# Verifica che:
```
- [ ] Contenga solo query SQL
- [ ] Usi decorator @with_rls_context
- [ ] Non contenga business logic
- [ ] Restituisca dict o valori semplici

### 2. Decorator RLS

**Verifica in core/decorators.py**:
- [ ] Decorator configura ruolo `authenticated`
- [ ] Decorator configura claim JWT
- [ ] Decorator gestisce commit/rollback
- [ ] Commenti dettagliati presenti

**Verifica uso in repository**:
```python
# domains/tasks/repository.py
@with_rls_context  # <-- Deve essere presente su metodi che accedono tasks
def get_all_tasks(self, conn, username):
    ...
```
- [ ] `get_all_tasks` decorato
- [ ] `create_task` decorato
- [ ] `update_task` decorato
- [ ] `delete_task` decorato

---

## 📝 Verifica Documentazione

### 1. README.md
- [ ] Sezione "Struttura Progetto" aggiornata
- [ ] Sezione "Architettura a Layer" presente
- [ ] Decorator @with_rls_context documentato
- [ ] Esempi codice per ogni layer
- [ ] Guida "Come aggiungere nuovo dominio"
- [ ] Sezione Testing aggiornata

### 2. Commenti nei File
Verifica random sampling:
- [ ] `domains/auth/service.py` - commenti dettagliati in italiano
- [ ] `domains/tasks/repository.py` - commenti dettagliati in italiano
- [ ] `core/decorators.py` - commenti dettagliati in italiano
- [ ] Tutti i metodi hanno docstring

### 3. File di Riepilogo
- [ ] `REFACTORING_SUMMARY.md` presente e completo
- [ ] `POST_REFACTORING_CHECKLIST.md` presente (questo file)

---

## 🚀 Deploy Preparation

### 1. Variabili Ambiente
Verifica che il file `.env` contenga (NON committare!):
```env
DATABASE_URL=postgresql://...
SECRET_KEY=...
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
```

### 2. Requirements
```bash
# Verifica che requirements.txt sia aggiornato
pip freeze > requirements_freeze.txt
# Confronta con requirements.txt esistente
```

### 3. Runtime
```bash
# Verifica runtime.txt
cat runtime.txt
# Dovrebbe essere: python-3.11.x o simile
```

---

## 🧪 Test Suite (Futuro)

**Da implementare** (struttura già presente):

```bash
# Quando i test saranno implementati:
pytest tests/ -v
pytest tests/test_auth.py -v
pytest tests/test_tasks.py -v
pytest --cov=domains --cov-report=html
```

**File da implementare**:
- [ ] Fixtures in `tests/conftest.py`
- [ ] Test Repository in `test_auth.py` e `test_tasks.py`
- [ ] Test Service in `test_auth.py` e `test_tasks.py`
- [ ] Test API in `test_auth.py` e `test_tasks.py`
- [ ] Test RLS specifici in `test_tasks.py`

---

## 🎯 Checklist Rapida

### Minimo Vitale (da fare subito)
- [ ] Server si avvia senza errori
- [ ] Swagger UI è accessibile
- [ ] Registrazione funziona
- [ ] Login restituisce JWT
- [ ] CRUD tasks funziona con autenticazione

### Consigliato (prima del deploy)
- [ ] Test RLS manuale con psql
- [ ] Verifica separazione layer
- [ ] Verifica decorator su tutti i metodi repository
- [ ] Review commenti e documentazione

### Opzionale (miglioramenti futuri)
- [ ] Implementare test automatici
- [ ] Logging strutturato
- [ ] Monitoring e metriche
- [ ] Cache layer

---

## 📞 Troubleshooting

### Errore: "Module not found"
```bash
# Verifica import
python -c "from domains.auth import router"
python -c "from domains.tasks import service"
python -c "from core.decorators import with_rls_context"
```

### Errore: "No module named 'domains'"
```bash
# Verifica __init__.py presenti
ls domains/__init__.py
ls domains/auth/__init__.py
ls domains/tasks/__init__.py
```

### Errore RLS: "Row not found"
- Verifica che decorator @with_rls_context sia applicato
- Verifica che username nel JWT corrisponda a utente nel DB
- Testa con psql manualmente (vedi sezione Test RLS)

### Server non si avvia
- Verifica requirements installati: `pip list`
- Verifica variabili ambiente: `echo $DATABASE_URL`
- Controlla log per dettagli errore

---

## ✨ Conclusione

Seguendo questa checklist, potrai verificare che il refactoring sia stato completato correttamente e che il backend funzioni come previsto.

**Prossimi passi consigliati**:
1. ✅ Verifica minimo vitale
2. 🧪 Test funzionali completi
3. 📊 Review architettura
4. 🚀 Deploy su ambiente staging
5. 🧪 Implementare test suite automatica

**Buon lavoro!** 🎉

