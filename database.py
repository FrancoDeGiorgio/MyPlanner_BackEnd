"""
Gestione connessione database e query protette da RLS.
"""
import os
import time
from typing import Optional
from urllib.parse import urlparse
from uuid import UUID

import psycopg2
from fastapi import HTTPException, status


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

    # Permetti override dei parametri di connessione via env per supportare ambienti diversi
    sslmode = os.getenv("DB_SSLMODE", "require")
    db_options = os.getenv("DB_OPTIONS", "-c pool_timeout=0")

    # Prepara i parametri di connessione
    conn_params = {
        'database': url.path[1:],
        'user': url.username,
        'password': url.password,
        'host': url.hostname,
        'port': url.port or 5432,  # Usa 5432 come fallback, ma vogliamo 6543
    }

    if sslmode:
        # In ambienti gestiti (Supabase/Render) è tipicamente 'require'.
        # In locale/container si può impostare a 'disable'.
        conn_params['sslmode'] = sslmode

    if db_options:
        # Opzione necessaria per PgBouncer su Supabase, disattivabile in locale.
        conn_params['options'] = db_options

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

            result = None
            if fetch_one:
                result = cur.fetchone()
            elif fetch_all:
                result = cur.fetchall()

            conn.commit()

            return result
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

