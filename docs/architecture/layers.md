# Layer Pattern - Dettaglio Implementazione

**Ultimo aggiornamento**: 2025-11-06

## 📚 Layer Architecture

Ogni layer ha responsabilità specifiche e comunica solo con layer adiacenti.

## 1️⃣ Presentation Layer (`app/api/`)

### Responsabilità
- Gestione richieste HTTP
- Validazione input tramite Pydantic
- Serializzazione output JSON
- Gestione autenticazione/autorizzazione
- Error handling HTTP

### Componenti

#### Routes (`app/api/routes/`)
```python
# auth.py
@router.post("/register")
def register_user(user: UserCreate, conn = Depends(get_db_conn)):
    # Delega al service
    return auth_service.register_user(conn, user.name_user, user.password)
```

**NON DEVE**:
- ❌ Contenere business logic
- ❌ Fare query SQL dirette
- ❌ Implementare regole di business

**DEVE**:
- ✅ Validare input con Pydantic
- ✅ Delegare ai service
- ✅ Restituire status code appropriati

#### Middleware (`app/api/middleware/`)
- **CORS**: Configurazione cross-origin
- **Error Handler**: Gestione eccezioni centralizzata
- **Rate Limiting** (futuro): Throttling richieste

#### Dependencies (`app/api/dependencies.py`)
```python
def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    # Estrae e valida JWT
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload.get("sub")
```

---

## 2️⃣ Business Logic Layer (`app/services/`)

### Responsabilità
- Implementazione regole di business
- Orchestrazione operazioni complesse
- Coordinamento tra repository
- Validazione business rules
- Mapping tra DTO e domain models

### Componenti

#### AuthService
```python
class AuthService:
    def register_user(self, conn, name_user, password):
        # 1. Business logic: hash password
        hashed = hash_password(password)
        
        # 2. Delega al repository
        user_id = self.repository.create_user(conn, name_user, hashed)
        
        # 3. Restituisce risultato
        return {"message": "User registered", "user_id": str(user_id)}
```

#### TaskService
```python
class TaskService:
    def create_task(self, conn, username, task_create):
        # 1. Business rule: recupera tenant_id
        tenant_id = self.user_repo.get_user_id_by_username(conn, username)
        
        # 2. Validazione: utente deve esistere
        if not tenant_id:
            raise HTTPException(404, "User not found")
        
        # 3. Delega al repository
        task_dict = self.task_repo.create_task(conn, username, tenant_id, ...)
        
        # 4. Mapping: dict → Pydantic Task
        return Task(**task_dict)
```

**NON DEVE**:
- ❌ Fare query SQL dirette
- ❌ Gestire richieste HTTP
- ❌ Conoscere dettagli database

**DEVE**:
- ✅ Implementare regole di business
- ✅ Orchestrare repository
- ✅ Validare business constraints
- ✅ Gestire transazioni complesse

---

## 3️⃣ Data Access Layer (`app/repositories/`)

### Responsabilità
- Esecuzione query SQL
- Gestione transazioni
- Applicazione RLS context
- Mapping risultati → dict
- Error handling database

### Componenti

#### BaseRepository (astratto)
```python
class BaseRepository(ABC):
    def _execute_query(self, conn, query, params, fetch_one, fetch_all):
        # Utility per esecuzione query standard
        # Gestisce cursor, commit, rollback
        pass
    
    def _check_exists(self, conn, field, value):
        # Verifica esistenza record
        pass
```

#### UserRepository
```python
class UserRepository:
    @staticmethod
    def create_user(conn, name_user, hashed_password):
        # Query SQL con RETURNING
        cur.execute("""
            INSERT INTO users (name_user, hashed_password)
            VALUES (%s, %s) RETURNING id
        """, (name_user, hashed_password))
        
        conn.commit()
        return cur.fetchone()[0]
```

#### TaskRepository (con RLS)
```python
class TaskRepository:
    @with_rls_context
    def create_task(self, conn, username, tenant_id, ...):
        # @with_rls_context applica automaticamente RLS
        cur.execute("""
            INSERT INTO tasks (...) VALUES (...) RETURNING *
        """, (...))
        return self._row_to_dict(cur.fetchone())
```

**NON DEVE**:
- ❌ Contenere business logic
- ❌ Conoscere dettagli HTTP
- ❌ Validare business rules

**DEVE**:
- ✅ Eseguire query SQL
- ✅ Applicare RLS quando necessario
- ✅ Gestire transazioni
- ✅ Mappare risultati

---

## 4️⃣ Domain Models Layer (`app/models/`)

### Responsabilità
- Rappresentare entità di business
- Contenere metodi di dominio
- Incapsulare logica di dominio pura
- Essere indipendenti da database/API

### Componenti

#### User (dataclass)
```python
@dataclass
class User:
    id: UUID
    name_user: str
    hashed_password: str
    created_at: datetime
```

#### Task (rich domain model)
```python
@dataclass
class Task:
    id: UUID
    tenant_id: UUID
    title: str
    # ... altri campi
    
    def get_effective_duration(self) -> Optional[int]:
        """Calcola durata effettiva (business logic)"""
        if self.duration_minutes:
            return self.duration_minutes
        if self.end_time:
            return (self.end_time - self.date_time).seconds // 60
        return None
    
    def is_overdue(self, current_time: datetime) -> bool:
        """Verifica se task è in ritardo (business logic)"""
        if self.completed:
            return False
        deadline = self.end_time or self.date_time
        return deadline < current_time
```

**NON DEVE**:
- ❌ Dipendere da database
- ❌ Dipendere da framework web
- ❌ Contenere SQL

**DEVE**:
- ✅ Rappresentare concetti di business
- ✅ Contenere logica di dominio
- ✅ Essere testabile in isolamento

---

## 5️⃣ DTO Layer (`app/schemas/`)

### Responsabilità
- Validazione input API
- Serializzazione output API
- Documentazione OpenAPI
- Conversione tipi

### Componenti

#### Pydantic Schemas
```python
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=1, max_length=255)
    color: ColorLiteral = Field(default="green")
    date_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=5, le=1440)
    completed: bool = False
    
    @model_validator(mode="after")
    def check_constraints(self):
        # Validazioni cross-field
        if self.end_time and self.duration_minutes:
            raise ValueError("Specifica solo end_time o duration_minutes")
        return self
```

**NON DEVE**:
- ❌ Contenere business logic
- ❌ Fare query database
- ❌ Essere usato nel dominio

**DEVE**:
- ✅ Validare formato dati
- ✅ Documentare API
- ✅ Convertire tipi
- ✅ Serializzare JSON

---

## 6️⃣ Core Layer (`app/core/`)

### Responsabilità
- Configurazione applicazione
- Connessioni database
- Sicurezza (JWT, hashing)
- Eccezioni custom

### Componenti

#### Config
```python
DATABASE_URL = os.environ.get("DATABASE_URL", "fallback")
SECRET_KEY = os.environ.get("SECRET_KEY", "fallback")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

#### Security
```python
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

#### Database
```python
def get_db_conn() -> Generator:
    # Generator per dependency injection
    conn = psycopg2.connect(...)
    try:
        yield conn
    finally:
        conn.close()
```

---

## 7️⃣ Utils Layer (`app/utils/`)

### Responsabilità
- Decoratori condivisi
- Logging
- Validatori riusabili
- Helper functions

### Componenti

#### Decorators
```python
@with_rls_context
def repository_method(conn, username, ...):
    # RLS context applicato automaticamente
    pass
```

#### Logger
```python
logger = get_logger(__name__)
logger.info("Operation completed", extra={"user_id": "123"})
```

---

## 🔄 Comunicazione tra Layer

### Regole
1. **Top-Down**: Layer superiori chiamano layer inferiori
2. **No Skip**: Non saltare layer (router → service → repository)
3. **DTO Boundaries**: Usare DTO ai confini (API ↔ Service)
4. **Domain Pure**: Domain models indipendenti

### Diagramma Dipendenze
```
Router → Service → Repository → Database
  ↓        ↓           ↓
Schemas  Models     Utils/Core
```

---

## 📝 Best Practices

### DO ✅
- Mantieni layer sottili e focalizzati
- Usa dependency injection
- Testa ogni layer separatamente
- Documenta responsabilità
- Gestisci errori per layer

### DON'T ❌
- Non mescolare responsabilità
- Non saltare layer
- Non creare dipendenze cicliche
- Non duplicare logica tra layer
- Non esporre dettagli interni

---

**Prossimo**: Leggi [Implementazione RLS](rls_implementation.md) per dettagli su Row-Level Security.

