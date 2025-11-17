"""
Gestione connessione database con SQLAlchemy ORM.

Questo modulo fornisce:
- Engine SQLAlchemy per connessione al database PostgreSQL
- SessionLocal factory per creare sessioni database
- Dependency injection per FastAPI (get_db)
- Event listener automatico per Row-Level Security (RLS)

Row-Level Security (RLS):
    Le policy RLS su PostgreSQL vengono attivate automaticamente tramite
    un event listener che configura il contesto JWT prima di ogni query.
    Ogni query viene eseguita con il contesto dell'utente autenticato,
    garantendo l'isolamento dei dati tra tenant.
"""
import os
from typing import Generator
from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import DATABASE_URL

# --- CONFIGURAZIONE ENGINE ---
# Crea engine SQLAlchemy per la connessione al database
# pool_pre_ping: verifica che le connessioni siano valide prima dell'uso
# echo: se True, logga tutte le query SQL (utile per debug)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verifica connessioni prima dell'uso
    echo=False,  # Disabilitato in prod, abilitare per debug
)

# --- CONFIGURAZIONE SESSION FACTORY ---
# SessionLocal è una factory che crea nuove sessioni database
# autocommit=False: le transazioni devono essere committate esplicitamente
# autoflush=False: i flush avvengono solo prima di query o commit espliciti
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# --- BASE PER MODELLI ORM ---
# Base è la classe base per tutti i modelli SQLAlchemy
# Tutti i modelli erediteranno da questa classe
Base = declarative_base()


# --- ROW-LEVEL SECURITY (RLS) EVENT LISTENER ---
@event.listens_for(Engine, "before_cursor_execute", retval=False)
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    """
    Event listener che configura automaticamente il contesto RLS prima di ogni query.
    
    Questo listener viene chiamato automaticamente da SQLAlchemy prima di eseguire
    qualsiasi query SQL. Se la sessione ha un username associato (tramite info['username']),
    configura il contesto PostgreSQL necessario per attivare le policy RLS.
    
    Il contesto RLS richiede:
    1. SET role authenticated - attiva le policy RLS
    2. set_config('request.jwt.claim.sub', username) - identifica il tenant
    3. set_config('request.jwt.claim.role', 'authenticated') - conferma il ruolo
    
    Args:
        conn: Connessione SQLAlchemy
        cursor: Cursore psycopg2
        statement: SQL statement da eseguire
        params: Parametri della query
        context: Contesto esecuzione SQLAlchemy
        executemany: Flag per esecuzione multipla
    
    Note:
        - L'username viene passato tramite session.info['username']
        - Se username non è presente, le query vengono eseguite senza RLS
        - Questo è utile per operazioni di sistema o migrazioni
    """
    # Recupera l'execution context dalla connessione SQLAlchemy
    execution_options = context.execution_options if context else {}
    
    # Cerca l'username nel contesto (impostato dai repository tramite db.info['username'])
    username = execution_options.get('username')
    
    if username:
        # --- STEP 1: Imposta il ruolo PostgreSQL ---
        # Questo attiva le policy RLS sulla connessione corrente
        cursor.execute("SET role authenticated;")
        
        # --- STEP 2: Imposta il claim JWT 'sub' (subject) ---
        # La funzione get_current_tenant_id() nel DB legge questo valore
        # per determinare quale tenant sta facendo la richiesta
        cursor.execute(
            "SELECT set_config('request.jwt.claim.sub', %s, true)",
            (username,)
        )
        
        # --- STEP 3: Imposta il claim JWT 'role' ---
        # Alcune policy verificano anche il ruolo per sicurezza extra
        cursor.execute(
            "SELECT set_config('request.jwt.claim.role', 'authenticated', true)"
        )


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection per FastAPI che fornisce una sessione database.
    
    Questa funzione è un generator che:
    1. Crea una nuova sessione database all'inizio della richiesta
    2. La passa all'endpoint tramite dependency injection
    3. Chiude automaticamente la sessione alla fine della richiesta
    
    Usage in FastAPI endpoints:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    
    Yields:
        Session: Sessione SQLAlchemy per operazioni database
    
    Note:
        - La sessione viene automaticamente chiusa dal finally
        - Le transazioni devono essere committate esplicitamente (db.commit())
        - In caso di errore, fare rollback manualmente (db.rollback())
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- FUNZIONI HELPER PER RLS ---
def set_rls_context(db: Session, username: str) -> None:
    """
    Imposta il contesto RLS per una sessione database.
    
    Questa funzione configura la sessione per includere l'username
    nelle execution options, che verrà poi utilizzato dall'event listener
    per configurare il contesto PostgreSQL RLS.
    
    Args:
        db: Sessione SQLAlchemy
        username: Username dell'utente autenticato
    
    Usage:
        db = SessionLocal()
        set_rls_context(db, "mario_rossi")
        tasks = db.query(Task).all()  # Vede solo le task di mario_rossi
    
    Note:
        - Questa funzione è opzionale, i repository possono impostare
          il contesto direttamente con db.info['username'] = username
        - L'event listener legge automaticamente questo valore
    """
    # Imposta l'username nella sessione per l'event listener
    db.info['username'] = username
    
    # Configura anche le execution options per propagare il contesto
    db.connection(execution_options={'username': username})
