"""
Repository Layer per il dominio Auth.

Responsabile dell'accesso ai dati per la tabella 'users'.
Gestisce tutte le query SQL relative agli utenti, nascondendo
i dettagli di implementazione del database ai layer superiori.
"""
from typing import Optional, Dict
from uuid import UUID
import psycopg2
from fastapi import HTTPException, status


class UserRepository:
    """
    Repository per la gestione degli utenti nel database.
    
    Questo repository incapsula tutte le operazioni CRUD sulla tabella 'users',
    fornendo un'interfaccia pulita per il Service Layer.
    
    IMPORTANTE: Questo repository NON usa il decorator @with_rls_context perché
    la tabella 'users' non ha policy RLS attive. Le operazioni su 'users' sono
    gestite direttamente a livello applicativo (auth service).
    """
    
    @staticmethod
    def create_user(conn: psycopg2.connect, name_user: str, hashed_password: str) -> UUID:
        """
        Crea un nuovo utente nel database.
        
        Inserisce un nuovo record nella tabella 'users' con username e password hashata.
        L'ID viene generato automaticamente dal database usando gen_random_uuid().
        
        Args:
            conn: Connessione psycopg2 al database
            name_user: Username univoco dell'utente (usato anche come tenant identifier)
            hashed_password: Password già hashata tramite bcrypt (mai salvare password in chiaro!)
        
        Returns:
            UUID: ID univoco del nuovo utente creato
        
        Raises:
            HTTPException 400: Se l'username esiste già (violazione constraint UNIQUE)
            HTTPException 500: Per altri errori database
        
        Note:
            - La colonna 'created_at' viene popolata automaticamente con NOW()
            - Il commit viene gestito dal chiamante (service layer o router)
        """
        try:
            with conn.cursor() as cur:
                # INSERT con RETURNING per ottenere l'ID generato
                cur.execute(
                    """
                    INSERT INTO users (name_user, hashed_password)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (name_user, hashed_password)
                )
                # Estrae l'UUID dalla prima colonna della riga restituita
                user_id = cur.fetchone()[0]

                # Commit esplicito: psycopg2 non usa autocommit di default.
                # Senza questo commit la registrazione viene persa a fine richiesta.
                conn.commit()
                
                return UUID(user_id) if isinstance(user_id, str) else user_id
                
        except psycopg2.errors.UniqueViolation:
            # L'username esiste già nel database
            conn.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists. Please choose a different username."
            )
        except Exception as e:
            # Errore generico durante l'inserimento
            conn.rollback()
            print(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user. Please try again later."
            )
    
    @staticmethod
    def get_user_by_username(conn: psycopg2.connect, username: str) -> Optional[Dict[str, any]]:
        """
        Recupera un utente completo dal database tramite username.
        
        Questa funzione viene usata principalmente durante il login per
        verificare le credenziali (confrontando la password hashata).
        
        Args:
            conn: Connessione psycopg2 al database
            username: Username dell'utente da cercare
        
        Returns:
            Optional[Dict]: Dizionario con i dati dell'utente se trovato, None altrimenti
                            Keys: 'id', 'name_user', 'hashed_password', 'created_at'
        
        Raises:
            HTTPException 500: In caso di errore durante la query
        
        Note:
            - Restituisce anche l'hashed_password per permettere la verifica
            - Non solleva 404 se l'utente non esiste, ritorna semplicemente None
              (la gestione del "utente non trovato" è delegata al service)
        """
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name_user, hashed_password, created_at
                    FROM users
                    WHERE name_user = %s
                    """,
                    (username,)
                )
                result = cur.fetchone()
                
                if result is None:
                    return None
                
                # Mappa la tupla risultato in un dizionario per facilità d'uso
                return {
                    'id': UUID(result[0]) if isinstance(result[0], str) else result[0],
                    'name_user': result[1],
                    'hashed_password': result[2],
                    'created_at': result[3]
                }
                
        except Exception as e:
            print(f"Error fetching user by username: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user information."
            )
    
    @staticmethod
    def get_user_id_by_username(conn: psycopg2.connect, username: str) -> Optional[UUID]:
        """
        Recupera solo l'ID di un utente tramite username.
        
        Versione ottimizzata che restituisce solo l'UUID, utile quando
        serve il tenant_id per creare task o altre entità associate all'utente.
        
        Args:
            conn: Connessione psycopg2 al database
            username: Username dell'utente
        
        Returns:
            Optional[UUID]: UUID dell'utente se trovato, None altrimenti
        
        Raises:
            HTTPException 500: In caso di errore durante la query
        
        Note:
            - Più efficiente di get_user_by_username quando serve solo l'ID
            - Usata principalmente quando si crea una task per ottenere il tenant_id
        """
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE name_user = %s
                    """,
                    (username,)
                )
                result = cur.fetchone()
                
                if result is None:
                    return None
                
                # Converte a UUID se necessario
                return UUID(result[0]) if isinstance(result[0], str) else result[0]
                
        except Exception as e:
            print(f"Error fetching user ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user ID."
            )

