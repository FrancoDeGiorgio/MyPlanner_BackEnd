"""
Service Layer per il dominio Auth.

Contiene la business logic per autenticazione, registrazione e gestione JWT.
Coordina le operazioni tra Repository Layer e API Layer, orchestrando
le chiamate a security utilities e database.
"""
from datetime import timedelta
from typing import Dict
import psycopg2

from config import ACCESS_TOKEN_EXPIRE_MINUTES
from security import hash_password, verify_password, create_access_token
from domains.auth.repository import UserRepository


class AuthService:
    """
    Service che gestisce la logica di business per l'autenticazione.
    
    Responsabilità:
    - Registrazione nuovi utenti (hashing password, validazione)
    - Autenticazione utenti (verifica credenziali, generazione JWT)
    - Coordinamento tra repository, security utilities e business rules
    
    IMPORTANTE: Il service NON conosce i dettagli SQL o della struttura database.
    Delega tutto l'accesso ai dati al UserRepository.
    """
    
    def __init__(self):
        """
        Inizializza il service con un'istanza del repository.
        
        In futuro potrebbe ricevere dipendenze via dependency injection
        (es. per testing con mock repository).
        """
        self.repository = UserRepository()
    
    def register_user(self, conn: psycopg2.connect, name_user: str, password: str) -> Dict[str, any]:
        """
        Registra un nuovo utente nel sistema.
        
        Questa funzione orchestra il processo di registrazione:
        1. Hash della password in chiaro (usando bcrypt)
        2. Salvataggio dell'utente nel database tramite repository
        3. Restituzione del risultato con messaggio di successo
        
        Args:
            conn: Connessione al database
            name_user: Username scelto dall'utente (deve essere univoco)
            password: Password in chiaro fornita dall'utente
        
        Returns:
            Dict: Dizionario con messaggio di successo e ID del nuovo utente
                  {"message": "User registered successfully", "user_id": UUID}
        
        Raises:
            HTTPException 400: Se l'username esiste già (propagato dal repository)
            HTTPException 500: Per altri errori durante la registrazione
        
        Note:
            - La password viene SEMPRE hashata prima di essere salvata
            - Il repository gestisce la verifica di unicità dell'username
            - Il commit è gestito dal repository
        
        Security:
            - Usa bcrypt per hashing (tramite passlib in security.py)
            - Mai salvare o loggare password in chiaro
        """
        # STEP 1: Hash della password usando bcrypt
        # La funzione hash_password in security.py usa passlib con bcrypt
        # che genera automaticamente un salt e applica molte iterazioni
        hashed_password = hash_password(password)
        
        # STEP 2: Delega al repository la creazione dell'utente
        # Il repository si occupa della query SQL e della gestione errori DB
        user_id = self.repository.create_user(
            conn=conn,
            name_user=name_user,
            hashed_password=hashed_password
        )
        
        # STEP 3: Restituisce il risultato in formato standardizzato
        return {
            "message": "User registered successfully",
            "user_id": str(user_id)  # Converte UUID a stringa per JSON
        }
    
    def authenticate_user(
        self,
        conn: psycopg2.connect,
        username: str,
        password: str
    ) -> Dict[str, str]:
        """
        Autentica un utente e genera un token JWT.
        
        Processo di autenticazione:
        1. Recupera l'utente dal database tramite username
        2. Verifica che l'utente esista
        3. Verifica che la password corrisponda all'hash salvato
        4. Genera un token JWT valido con claim appropriati
        5. Restituisce il token per uso nei successivi endpoint protetti
        
        Args:
            conn: Connessione al database
            username: Username fornito dall'utente
            password: Password in chiaro fornita dall'utente
        
        Returns:
            Dict: Token JWT e tipo di token
                  {"access_token": "eyJ...", "token_type": "bearer"}
        
        Raises:
            HTTPException 401: Se username non esiste o password è errata
            HTTPException 500: Per errori durante il recupero utente o generazione token
        
        Note:
            - Il token JWT contiene il claim 'sub' con l'username
            - Il claim 'sub' sarà poi usato per configurare il contesto RLS
            - Il token ha una scadenza configurabile (ACCESS_TOKEN_EXPIRE_MINUTES)
        
        Security:
            - Usa verify_password per confronto timing-safe tra password e hash
            - Restituisce sempre lo stesso errore per username/password errati
              (per non rivelare se un username esiste o no - security best practice)
        """
        from fastapi import HTTPException, status
        
        # STEP 1: Recupera l'utente dal database
        user = self.repository.get_user_by_username(conn, username)
        
        # STEP 2: Verifica che l'utente esista
        if user is None:
            # Utente non trovato - restituisce errore generico
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # STEP 3: Verifica la password
        # verify_password usa bcrypt per confrontare in modo sicuro (timing-safe)
        # la password fornita con l'hash salvato nel database
        if not verify_password(password, user['hashed_password']):
            # Password errata - restituisce lo stesso errore generico
            # (per non rivelare che l'username esiste)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # STEP 4: Genera il token JWT
        # Il token conterrà:
        # - 'sub' (subject): l'username, usato poi per RLS
        # - 'exp' (expiration): timestamp di scadenza
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username},  # CRITICO: 'sub' deve contenere l'username!
            expires_delta=access_token_expires
        )
        
        # STEP 5: Restituisce il token in formato OAuth2 standard
        return {
            "access_token": access_token,
            "token_type": "bearer"  # Lowercase per standard OAuth2
        }

