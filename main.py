import os
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urlparse


import psycopg2
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from jose import JWTError, jwt
from uuid import UUID
import time


# --- CARICAMENTO VARIABILI D'AMBIENTE (SOLO PER SVILUPPO LOCALE/FALLBACK) ---
# Render inietterà queste variabili nell'ambiente
try:
    # Usiamo dotenv solo se è installato e se stiamo caricando localmente
    from dotenv import load_dotenv
    if not os.environ.get("RENDER"): # Non caricare da .env se siamo su Render
        load_dotenv()
except ImportError:
    pass

# --- CONFIGURAZIONE E VARIABILI D'AMBIENTE ---
# CRITICO: Render DEVE fornire queste variabili!
# Userà il valore di Render se esiste, altrimenti il fallback.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:fallback_password@fallback_host:5432/postgres" # Fallback sicuro
)

SECRET_KEY = os.environ.get("SECRET_KEY", "IL_TUO_SEGRETO_JWT_SUPER_SICURO_FALLBACK") # Fallback sicuro
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Per l'hashing delle password
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto"
    )

# Schema per l'autenticazione OAuth2 (per la dependency)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# --- MODELLI Pydantic (SCHEMI DATI) ---

class Token(BaseModel):
    """Schema per il token JWT restituito dopo il login."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema per i dati contenuti nel JWT (il 'sub' è il name_user)."""
    username: Optional[str] = None

class UserBase(BaseModel):
    """Schema di base per l'utente (usato per login/registrazione)."""
    name_user: str = Field(..., description="Nome utente unico (usato come Subject JWT)")

class UserCreate(UserBase):
    """Schema per la registrazione."""
    password: str

class TaskBase(BaseModel):
    """Schema di base per l'attività."""
    description: str = Field(..., min_length=1, max_length=255)
    date_time: datetime
    completed: bool = False

class TaskCreate(TaskBase):
    """Schema per la creazione di una nuova attività."""
    pass # Nessun tenant_id in input: il backend lo imposta!

class Task(TaskBase):
    """Schema completo dell'attività (inclusi gli ID di sistema)."""
    id: UUID
    tenant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- FUNZIONI DI SICUREZZA (JWT e Hashing) ---

def hash_password(password: str):
    """Genera l'hash della password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verifica la corrispondenza della password in chiaro con l'hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency per estrarre il nome utente dal JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Il claim 'sub' (subject) contiene l'username
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    return token_data.username

# --- FUNZIONI DATABASE E RLS ---

def get_db_conn():
    """
    Stabilisce una connessione al database PostgreSQL.
    
    Questa versione usa 'urllib.parse' per analizzare l'URI del database, 
    aggiungendo forzatamente il parametro 'options' necessario per 
    PgBouncer di Supabase in modo da evitare l'errore di sintassi
    di psycopg2 che ha bloccato i deploy precedenti.
    """
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if not DATABASE_URL:
        # Questo non dovrebbe succedere su Render, ma è una buona pratica
        raise ValueError("DATABASE_URL non è impostata.")

    # Analizza l'URI del database
    url = urlparse(DATABASE_URL)
    
    # Prepara i parametri di connessione
    conn_params = {
        'database': url.path[1:],
        'user': url.username,
        'password': url.password,
        'host': url.hostname,
        'port': url.port or 5432, # Usa 5432 come fallback, ma vogliamo 6543
        
        # PARAMETRI CRITICI AGGIUNTI MANUALMENTE
        # 1. Forza SSL, necessario per Supabase/Render
        'sslmode': 'require',
        # 2. Forza l'opzione PgBouncer per risolvere l'errore SASL.
        # Questa opzione non può essere passata correttamente nella query string 
        # dell'URI a causa di un bug di parsing di psycopg2.
        'options': '-c pool_timeout=0'
    }

    conn = None
    max_retries = 5
    for attempt in range(max_retries):
        try:
            # Connettiti usando i parametri estratti
            conn = psycopg2.connect(**conn_params)
            break
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1 and "FATAL: Tenant or user not found" not in str(e):
                print(f"Tentativo di riconnessione al DB fallito ({attempt + 1}/{max_retries}). Riprovo tra 2 secondi...")
                time.sleep(2)
            else:
                # Se è l'ultimo tentativo o è un errore di credenziali, fallisci
                raise e

    if conn is None:
        raise ConnectionError("Impossibile connettersi al database dopo i tentativi.")

    try:
        yield conn
    finally:
        conn.close()
def execute_protected_query(
    conn: psycopg2.connect,
    username: str,
    sql_query: str,
    params: Optional[tuple] = None,
    fetch_one: bool = False,
    fetch_all: bool = False,
):
    """
    Esegue una query protetta da RLS.
    CRITICO: Imposta il ruolo 'authenticated' e il contesto JWT
    prima di eseguire la query.
    """
    try:
        with conn.cursor() as cur:
            # 1. Imposta il ruolo 'authenticated' (per applicare le policy RLS)
            cur.execute("SET role authenticated;")
            # 2. Imposta il contesto JWT: 'sub' (subject) = username
            # Questa è la chiave per far funzionare get_current_tenant_id() in RLS!
            cur.execute("SELECT set_config('request.jwt.claim.sub', %s, true)", (username,))
            # 3. Imposta anche il claim 'role' se le policy Supabase lo verificano
            cur.execute("SELECT set_config('request.jwt.claim.role', 'authenticated', true)")
            
            # Esegui la query
            cur.execute(sql_query, params)
            
            if fetch_one:
                return cur.fetchone()
            if fetch_all:
                return cur.fetchall()
            
            conn.commit()
            return None
    except Exception as e:
        conn.rollback()
        print(f"Database Error: {e}")
        # In un ambiente di produzione, potresti voler loggare l'errore completo ma restituire solo un messaggio generico
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database operation failed. Check logs."
        )

def get_user_id_by_username(
    conn: psycopg2.connect,
    target_username: str,
    auth_username: Optional[str] = None,
) -> Optional[UUID]:
    """Recupera l'ID UUID di un utente per usarlo come tenant_id."""
    try:
        if auth_username:
            result = execute_protected_query(
                conn,
                auth_username,
                "SELECT id FROM users WHERE name_user = %s",
                (target_username,),
                fetch_one=True,
            )
        else:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE name_user = %s", (target_username,))
                result = cur.fetchone()

        if result:
            return UUID(result[0])
        return None
    except Exception as e:
        print(f"Error fetching user ID: {e}")
        # Gestione dell'errore di connessione o query
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve user ID."
        )


# --- INIZIALIZZAZIONE APP FASTAPI ---

app = FastAPI(
    title="Planner Attività Multi-Tenant (FastAPI + Supabase RLS)",
    description="Backend per la gestione delle attività protette da RLS."
)

# --- ENDPOINT DI AUTENTICAZIONE ---

@app.post("/auth/register", summary="Registra un nuovo utente/tenant")
def register_user(user: UserCreate, conn: psycopg2.connect = Depends(get_db_conn)):
    """Crea un nuovo utente nella tabella 'users'."""
    try:
        hashed_password = hash_password(user.password)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (name_user, hashed_password) VALUES (%s, %s) RETURNING id",
                (user.name_user, hashed_password)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return {"message": "User registered successfully", "user_id": user_id}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {e}"
        )

@app.post("/auth/login", response_model=Token, summary="Esegue il login e restituisce il JWT")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: psycopg2.connect = Depends(get_db_conn)
):
    """
    Verifica le credenziali e genera un token JWT.
    Il token contiene il 'name_user' nel claim 'sub', essenziale per l'RLS.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT hashed_password FROM users WHERE name_user = %s",
            (form_data.username,)
        )
        result = cur.fetchone()
        
        if result is None or not verify_password(form_data.password, result[0]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # CRITICO: Imposta 'sub' (subject) come l'username
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# --- ENDPOINT ATTIVITÀ (CRUD PROTETTO DA RLS) ---

@app.get("/tasks", response_model=List[Task], summary="Recupera tutte le attività del tenant")
def read_tasks(
    username: str = Depends(get_current_user),
    conn: psycopg2.connect = Depends(get_db_conn)
):
    """
    Restituisce solo le attività associate all'utente autenticato,
    grazie all'applicazione dell'RLS.
    """
    sql_query = "SELECT id, tenant_id, description, date_time, completed, created_at FROM tasks ORDER BY date_time DESC"
    
    # Esegue la query, impostando il contesto RLS
    results = execute_protected_query(conn, username, sql_query, fetch_all=True)
    
    if not results:
        return []

    # Mappa i risultati sul modello Pydantic Task
    tasks = []
    for row in results:
        try:
            tasks.append(Task(
                id=UUID(row[0]),
                tenant_id=UUID(row[1]),
                description=row[2],
                date_time=row[3],
                completed=row[4],
                created_at=row[5],
            ))
        except Exception as e:
            # Gestisce eventuali errori di conversione
            print(f"Error mapping task row: {e}")

    return tasks

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED, summary="Crea una nuova attività")
def create_task(
    task: TaskCreate,
    username: str = Depends(get_current_user),
    conn: psycopg2.connect = Depends(get_db_conn)
):
    """
    Crea una nuova attività. Il tenant_id viene letto dal database
    e iniettato automaticamente, come richiesto dalla RLS (Policy INSERT).
    """
    tenant_id = get_user_id_by_username(conn, username, auth_username=username)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant user not found in the system."
        )

    sql_query = """
    INSERT INTO tasks (tenant_id, description, date_time, completed) 
    VALUES (%s, %s, %s, %s) 
    RETURNING id, tenant_id, description, date_time, completed, created_at
    """
    params = (tenant_id, task.description, task.date_time, task.completed)
    
    # Esegue la query, impostando il contesto RLS
    result = execute_protected_query(conn, username, sql_query, params, fetch_one=True)
    
    if not result:
        # Se la riga non viene restituita, la creazione è fallita, probabilmente a causa di RLS
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task creation failed, possibly due to RLS violation (check policy on tenant_id)."
        )

    return Task(
        id=UUID(result[0]),
        tenant_id=UUID(result[1]),
        description=result[2],
        date_time=result[3],
        completed=result[4],
        created_at=result[5],
    )

@app.put("/tasks/{task_id}", response_model=Task, summary="Aggiorna un'attività esistente")
def update_task(
    task_id: UUID,
    task_update: TaskBase,
    username: str = Depends(get_current_user),
    conn: psycopg2.connect = Depends(get_db_conn)
):
    """
    Aggiorna un'attività esistente. L'RLS garantisce che l'utente possa
    modificare solo le proprie attività.
    """
    # Nota: NON stiamo permettendo di aggiornare il tenant_id, il che è
    # anche richiesto dalla clausola WITH CHECK della tua Policy UPDATE.

    sql_query = """
    UPDATE tasks 
    SET description = %s, date_time = %s, completed = %s 
    WHERE id = %s 
    RETURNING id, tenant_id, description, date_time, completed, created_at
    """
    params = (task_update.description, task_update.date_time, task_update.completed, task_id)

    # Esegue la query, impostando il contesto RLS
    result = execute_protected_query(conn, username, sql_query, params, fetch_one=True)

    if not result:
        # Se la riga non viene restituita, o l'ID non esiste, o l'utente non è il proprietario (RLS)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or you do not have permission to update it (RLS block)."
        )

    return Task(
        id=UUID(result[0]),
        tenant_id=UUID(result[1]),
        description=result[2],
        date_time=result[3],
        completed=result[4],
        created_at=result[5],
    )

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Elimina un'attività")
def delete_task(
    task_id: UUID,
    username: str = Depends(get_current_user),
    conn: psycopg2.connect = Depends(get_db_conn)
):
    """
    Elimina un'attività. L'RLS garantisce che l'utente possa
    cancellare solo le proprie attività.
    """
    sql_query = "DELETE FROM tasks WHERE id = %s RETURNING id"
    params = (task_id,)

    # Esegue la query, impostando il contesto RLS
    result = execute_protected_query(conn, username, sql_query, params, fetch_one=True)

    if not result:
        # Se la riga non viene restituita, o l'ID non esiste, o l'utente non è il proprietario (RLS)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or you do not have permission to delete it (RLS block)."
        )

    return
