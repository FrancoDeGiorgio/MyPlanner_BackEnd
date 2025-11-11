# Linee Guida per Contribuire

**Ultimo aggiornamento**: 2025-11-06

## 🎯 Processo di Contribuzione

### 1. Prima di Iniziare
- Leggi la [Panoramica Architettura](../architecture/overview.md)
- Familiarizza con il [Layer Pattern](../architecture/layers.md)
- Configura l'ambiente seguendo [Setup](setup.md)

### 2. Workflow
1. Crea un branch da `main`: `git checkout -b feature/nome-feature`
2. Implementa le modifiche
3. Aggiungi test
4. Aggiorna la documentazione
5. Esegui linting e test
6. Crea una Pull Request

## 📝 Checklist Pre-Commit

Prima di ogni commit, verifica:

### Code Quality
- [ ] Codice segue lo stile del progetto
- [ ] Nessun import non utilizzato
- [ ] Nessun codice commentato (rimuovi o documenta perché)
- [ ] Nessun TODO senza issue associata

### Documentazione
- [ ] **CRITICO**: Tutti i docstring sono in **italiano**
- [ ] Ogni funzione ha docstring completo
- [ ] Ogni classe ha docstring completo
- [ ] File markdown aggiornati se necessario
- [ ] README aggiornato se cambiamenti significativi

### Testing
- [ ] Tutti i test passano: `pytest`
- [ ] Nuove feature hanno test
- [ ] Coverage non diminuita
- [ ] Test di integrazione aggiornati se necessario

### Architettura
- [ ] Modifiche rispettano il layer pattern
- [ ] Nessuna violazione di separazione responsabilità
- [ ] Import path corretti (`app.*`)
- [ ] Nessuna dipendenza circolare

## 🏗️ Standard Codice

### Stile Python
- Segui **PEP 8**
- Usa **type hints** sempre
- Linea max 100 caratteri
- Import organizzati (stdlib → third-party → local)

### Naming Conventions
```python
# File: snake_case.py
# Classi: PascalCase
class UserService:
    pass

# Funzioni: snake_case
def create_user():
    pass

# Costanti: UPPER_CASE
MAX_RETRIES = 5

# Variabili: snake_case
user_name = "mario"
```

### Docstring (SEMPRE IN ITALIANO)

#### Modulo
```python
"""
Breve descrizione del modulo.

Descrizione più dettagliata se necessario.
Include responsabilità e uso principale.
"""
```

#### Funzione
```python
def create_task(conn, username, task_data):
    """
    Breve descrizione (una frase).
    
    Descrizione dettagliata del comportamento.
    Spiega il processo step-by-step se complesso.
    
    Args:
        conn: Connessione al database
        username: Username dell'utente autenticato
        task_data: Dati della task da creare
    
    Returns:
        Task: Task creata con tutti i campi
    
    Raises:
        HTTPException 404: Se l'utente non esiste
        HTTPException 500: Per errori database
    
    Example:
        >>> task = create_task(conn, "mario", task_data)
        >>> print(task.id)
        UUID('...')
    
    Note:
        - Il tenant_id viene determinato automaticamente
        - Usa RLS per isolamento multi-tenant
    """
    pass
```

#### Classe
```python
class TaskService:
    """
    Service per la gestione delle task.
    
    Responsabilità:
    - Creare nuove task
    - Aggiornare task esistenti
    - Eliminare task
    - Coordinare repository e validazioni
    
    IMPORTANTE: NON contiene query SQL dirette.
    Delega tutto l'accesso dati al TaskRepository.
    
    Attributes:
        task_repo: Repository per operazioni CRUD task
        user_repo: Repository per lookup utenti
    """
    pass
```

## 🎨 Commenti nel Codice

### Quando Commentare
```python
# ✅ BUONO: Spiega PERCHÉ, non COSA
# Usiamo bcrypt invece di argon2 per compatibilità con sistemi legacy
hashed = hash_password(password)

# ❌ CATTIVO: Ripete il codice
# Hasha la password
hashed = hash_password(password)
```

### Sezioni nel Codice
```python
# --- STEP 1: Validazione Input ---
if not username:
    raise ValueError("Username required")

# --- STEP 2: Recupero Dati ---
user = repository.get_user(username)

# --- STEP 3: Business Logic ---
if user.is_locked:
    raise UserLockedError()
```

## 📦 Aggiungere Nuove Feature

### 1. Nuovo Endpoint

#### a) Crea/Aggiorna Schema (DTO)
```python
# app/schemas/new_feature.py
class FeatureCreate(BaseModel):
    """Schema per creare una feature."""
    name: str = Field(..., min_length=1, max_length=100)
```

#### b) Crea/Aggiorna Model (Domain)
```python
# app/models/feature.py
@dataclass
class Feature:
    """Entità di dominio Feature."""
    id: UUID
    name: str
    created_at: datetime
```

#### c) Crea Repository
```python
# app/repositories/feature_repository.py
class FeatureRepository:
    """Repository per gestione feature."""
    
    @staticmethod
    def create_feature(conn, name):
        """Crea una nuova feature."""
        # Query SQL qui
        pass
```

#### d) Crea Service
```python
# app/services/feature_service.py
class FeatureService:
    """Service per business logic feature."""
    
    def __init__(self):
        self.repository = FeatureRepository()
    
    def create_feature(self, conn, name):
        """Crea feature con business logic."""
        # Business logic qui
        return self.repository.create_feature(conn, name)
```

#### e) Crea Router
```python
# app/api/routes/features.py
router = APIRouter(prefix="/features", tags=["Features"])
feature_service = FeatureService()

@router.post("", response_model=Feature)
def create_feature(
    feature: FeatureCreate,
    username: str = Depends(get_current_user),
    conn = Depends(get_db_conn)
):
    """Endpoint per creare feature."""
    return feature_service.create_feature(conn, feature.name)
```

#### f) Registra Router in main.py
```python
from app.api.routes import features

app.include_router(features.router)
```

#### g) Aggiungi Test
```python
# tests/integration/test_features.py
def test_create_feature():
    """Test creazione feature."""
    pass
```

#### h) Aggiorna Documentazione
- Aggiorna `docs/api/` con nuovo endpoint
- Aggiorna `docs/architecture/overview.md` se cambia struttura

### 2. Nuova Dipendenza

1. Aggiungi a `requirements.txt`
2. Documenta WHY in commit message
3. Aggiorna `docs/development/setup.md`
4. Verifica compatibilità versioni

### 3. Modifica Database

1. Crea migration Alembic (quando configurato)
2. Aggiorna repository corrispondente
3. Aggiorna model se cambia schema
4. Testa migration up e down

## ⚠️ Regole Importanti

### ❌ NON FARE MAI
- Committare credenziali o secrets
- Skippare test
- Modificare file senza commentare
- Creare dipendenze circolari
- Mescolare responsabilità tra layer
- Usare `import *`
- Lasciare `print()` per debug (usa logger)

### ✅ FARE SEMPRE
- Scrivere docstring in italiano
- Aggiungere type hints
- Testare le modifiche
- Aggiornare la documentazione
- Seguire il layer pattern
- Gestire le eccezioni appropriatamente

## 🧪 Testing

### Test Unitari
```python
# tests/unit/test_auth_service.py
def test_register_user_success():
    """Test registrazione utente con successo."""
    # Arrange
    mock_repo = MagicMock()
    service = AuthService()
    service.repository = mock_repo
    
    # Act
    result = service.register_user(conn, "user", "pass")
    
    # Assert
    assert result["message"] == "User registered successfully"
    mock_repo.create_user.assert_called_once()
```

### Test Integrazione
```python
# tests/integration/test_task_flow.py
def test_create_and_retrieve_task():
    """Test flusso completo creazione e recupero task."""
    # Test con database reale (test DB)
    pass
```

## 📚 Documentazione

### Quando Aggiornare
- ✅ Nuovi endpoint → `docs/api/`
- ✅ Cambio architettura → `docs/architecture/`
- ✅ Nuove procedure → `docs/development/`
- ✅ Decisioni architetturali → `docs/adr/`

### Template ADR
```markdown
# ADR XXX: Titolo Decisione

**Data**: YYYY-MM-DD
**Status**: Proposta | Accettata | Deprecata

## Contesto
Perché serviva una decisione?

## Decisione
Cosa abbiamo deciso?

## Conseguenze
Cosa implica questa decisione?

## Alternative Considerate
Quali altre opzioni c'erano?
```

## 🔍 Code Review

### Per Reviewer
- Verifica architettura rispettata
- Controlla test coverage
- Verifica documentazione aggiornata
- Testa localmente se possibile
- Sii costruttivo nei feedback

### Per Author
- Rispondi a tutti i commenti
- Non prendere feedback personalmente
- Spiega le tue scelte
- Aggiorna in base ai feedback

## 🎓 Risorse

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Clean Code Principles](https://clean-code-developer.com/)
- [Layer Architecture Pattern](../architecture/layers.md)

## 📧 Supporto

Per domande:
1. Cerca nella documentazione
2. Controlla issue esistenti
3. Chiedi nel team

---

**Grazie per contribuire a MyPlanner! 🚀**

