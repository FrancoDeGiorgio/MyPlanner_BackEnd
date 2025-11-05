"""
Decoratori condivisi per funzionalità trasversali.

Contiene principalmente il decorator @with_rls_context per gestire
automaticamente il contesto Row-Level Security di PostgreSQL/Supabase.
"""
from functools import wraps
from typing import Callable, Any, Optional
import psycopg2
from psycopg2.extensions import connection as PsycopgConnection
from fastapi import HTTPException, status


def with_rls_context(func: Callable) -> Callable:
    """
    Decorator che wrappa una funzione repository per applicare automaticamente
    il contesto Row-Level Security (RLS) prima di eseguire query al database.
    
    Questo decorator si occupa di:
    1. Impostare il ruolo PostgreSQL 'authenticated' per attivare le policy RLS
    2. Configurare il claim JWT 'sub' con l'username dell'utente autenticato
    3. Configurare il claim JWT 'role' come 'authenticated'
    4. Eseguire la funzione repository wrappata
    5. Gestire commit/rollback della transazione in caso di errore
    
    IMPORTANTE: Le funzioni decorate devono avere come primi due parametri:
    - conn: psycopg2.connect (connessione al database)
    - username: str (username dell'utente autenticato)
    
    Il decorator estrae questi parametri, configura il contesto RLS e poi
    chiama la funzione originale con tutti i suoi parametri.
    
    Row-Level Security (RLS):
    --------------------------
    RLS è una feature di PostgreSQL che permette di filtrare automaticamente
    le righe di una tabella in base a policy definite a livello di database.
    
    Nel nostro caso:
    - Le policy RLS su 'tasks' verificano che tenant_id corrisponda
      all'ID dell'utente ricavato dal claim JWT 'sub'
    - La funzione get_current_tenant_id() nel DB legge il claim 'sub'
      e restituisce l'UUID corrispondente
    - Ogni query SELECT/INSERT/UPDATE/DELETE viene automaticamente filtrata
    
    Usage:
    ------
    @with_rls_context
    def get_tasks(conn, username, status=None):
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE completed = %s", (status,))
            return cur.fetchall()
    
    # Quando chiamata, la funzione avrà automaticamente il contesto RLS attivo
    tasks = get_tasks(db_conn, "user123", status=False)
    
    Args:
        func: Funzione repository da decorare (deve accettare conn e username)
    
    Returns:
        Callable: Funzione wrappata con gestione automatica del contesto RLS
    
    Raises:
        HTTPException 500: Se si verifica un errore durante l'esecuzione della query
    """
    @wraps(func)
    def wrapper(*call_args, **kwargs) -> Any:
        """
        Wrapper interno che configura RLS ed esegue la funzione decorata.
        
        Args:
            call_args: Argomenti posizionali passati alla funzione decorata
            **kwargs: Argomenti keyword della funzione originale
        
        Returns:
            Any: Risultato della funzione repository originale
        """
        bound_self: Optional[Any] = None
        args_list = list(call_args)

        # --- STEP 0: Estrai self (se presente), conn e username ---
        if args_list:
            first_arg = args_list[0]
            if isinstance(first_arg, PsycopgConnection) or hasattr(first_arg, "cursor"):
                # Funzione standalone: il primo argomento è la connessione
                conn = args_list.pop(0)
            else:
                # Metodo di classe: il primo argomento è self
                bound_self = args_list.pop(0)
                if args_list:
                    conn = args_list.pop(0)
                else:
                    conn = kwargs.pop("conn", None)
        else:
            conn = kwargs.pop("conn", None)

        if conn is None:
            raise TypeError(
                f"{func.__name__}() requires a 'conn' argument complying with psycopg2 connection interface"
            )

        if not hasattr(conn, "cursor"):
            raise TypeError(
                f"Invalid connection object passed to {func.__name__}(): missing 'cursor' method"
            )

        if args_list:
            username = args_list.pop(0)
        else:
            username = kwargs.pop("username", None)

        if username is None:
            raise TypeError(
                f"{func.__name__}() requires a 'username' argument for RLS context"
            )
        try:
            with conn.cursor() as cur:
                # --- STEP 1: Imposta il ruolo PostgreSQL ---
                # Il ruolo 'authenticated' è quello su cui sono definite le policy RLS.
                # Senza questo, le policy non verrebbero applicate e l'utente
                # potrebbe vedere dati di altri tenant.
                cur.execute("SET role authenticated;")
                
                # --- STEP 2: Imposta il claim JWT 'sub' (subject) ---
                # Questo claim contiene l'username e viene usato dalla funzione
                # get_current_tenant_id() nel database per risalire all'UUID del tenant.
                # set_config() imposta una variabile di configurazione di sessione:
                # - primo parametro: nome della variabile ('request.jwt.claim.sub')
                # - secondo parametro: valore (username)
                # - terzo parametro: true = locale alla transazione corrente
                cur.execute(
                    "SELECT set_config('request.jwt.claim.sub', %s, true)",
                    (username,)
                )
                
                # --- STEP 3: Imposta il claim JWT 'role' ---
                # Alcune policy Supabase verificano anche il ruolo JWT.
                # Lo impostiamo a 'authenticated' per consistenza.
                cur.execute(
                    "SELECT set_config('request.jwt.claim.role', 'authenticated', true)"
                )
            
            # --- STEP 4: Esegui la funzione repository originale ---
            # A questo punto il contesto RLS è attivo e tutte le query
            # nella funzione repository saranno automaticamente filtrate
            if bound_self is not None:
                result = func(bound_self, conn, username, *args_list, **kwargs)
            else:
                result = func(conn, username, *args_list, **kwargs)
            
            # --- STEP 5: Commit della transazione ---
            # Se tutto è andato a buon fine, confermiamo le modifiche
            conn.commit()
            
            return result
            
        except psycopg2.Error as db_error:
            # Errore a livello database (violazione constraint, RLS block, ecc.)
            conn.rollback()
            print(f"Database Error in {func.__name__}: {db_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database operation failed in {func.__name__}. Check logs."
            )
        except HTTPException:
            # Se la funzione repository ha già lanciato una HTTPException,
            # la rilanciamo così com'è (es. 404 Not Found)
            conn.rollback()
            raise
        except Exception as e:
            # Errore generico non previsto
            conn.rollback()
            print(f"Unexpected Error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error in {func.__name__}. Check logs."
            )
    
    return wrapper

