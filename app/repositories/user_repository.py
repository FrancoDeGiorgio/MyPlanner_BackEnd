"""
Repository Layer per gli utenti (User) - SQLAlchemy ORM.

Responsabile dell'accesso ai dati per la tabella 'users'.
Gestisce tutte le operazioni CRUD relative agli utenti usando SQLAlchemy ORM.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.user import User


class UserRepository:
    """
    Repository per la gestione degli utenti nel database con SQLAlchemy ORM.
    
    Questo repository incapsula tutte le operazioni CRUD sulla tabella 'users',
    fornendo un'interfaccia pulita per il Service Layer.
    
    IMPORTANTE: Questo repository NON usa RLS perché la tabella 'users'
    non ha policy RLS attive. Le operazioni su 'users' sono gestite
    direttamente a livello applicativo (auth service).
    """
    
    @staticmethod
    def create_user(db: Session, name_user: str, hashed_password: str) -> User:
        """
        Crea un nuovo utente nel database.
        
        Inserisce un nuovo record nella tabella 'users' con username e password hashata.
        L'ID viene generato automaticamente dal database usando gen_random_uuid().
        
        Args:
            db: Sessione SQLAlchemy
            name_user: Username univoco dell'utente (usato anche come tenant identifier)
            hashed_password: Password già hashata tramite bcrypt (mai salvare password in chiaro!)
        
        Returns:
            User: Oggetto User ORM con l'ID generato
        
        Raises:
            HTTPException 400: Se l'username esiste già (violazione constraint UNIQUE)
            HTTPException 500: Per altri errori database
        
        Note:
            - La colonna 'created_at' viene popolata automaticamente dal database
            - Il commit viene eseguito automaticamente da questo metodo
        """
        try:
            # Crea nuova istanza del modello User
            new_user = User(
                name_user=name_user,
                hashed_password=hashed_password
            )
            
            # Aggiungi alla sessione
            db.add(new_user)
            
            # Commit per persistere nel database
            db.commit()
            
            # Refresh per ottenere i valori generati dal database (id, created_at)
            db.refresh(new_user)
            
            return new_user
            
        except IntegrityError as e:
            # L'username esiste già nel database (violazione UNIQUE constraint)
            db.rollback()
            
            # Verifica se è effettivamente un errore di username duplicato
            if 'name_user' in str(e.orig) or 'users_name_user_key' in str(e.orig):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists. Please choose a different username."
                )
            
            # Altro tipo di IntegrityError
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user due to database constraint."
            )
            
        except Exception as e:
            # Errore generico durante l'inserimento
            db.rollback()
            print(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user. Please try again later."
            )
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        Recupera un utente completo dal database tramite username.
        
        Questa funzione viene usata principalmente durante il login per
        verificare le credenziali (confrontando la password hashata).
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente da cercare
        
        Returns:
            Optional[User]: Oggetto User ORM se trovato, None altrimenti
        
        Raises:
            HTTPException 500: In caso di errore durante la query
        
        Note:
            - Restituisce anche l'hashed_password per permettere la verifica
            - Non solleva 404 se l'utente non esiste, ritorna semplicemente None
              (la gestione del "utente non trovato" è delegata al service)
        """
        try:
            user = db.query(User).filter(User.name_user == username).first()
            return user
            
        except Exception as e:
            print(f"Error fetching user by username: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user information."
            )
    
    @staticmethod
    def get_user_id_by_username(db: Session, username: str) -> Optional[UUID]:
        """
        Recupera solo l'ID di un utente tramite username.
        
        Versione ottimizzata che restituisce solo l'UUID, utile quando
        serve il tenant_id per creare task o altre entità associate all'utente.
        
        Args:
            db: Sessione SQLAlchemy
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
            # Query ottimizzata che recupera solo la colonna id
            result = db.query(User.id).filter(User.name_user == username).first()
            
            if result is None:
                return None
            
            # result è una tupla (id,), estraiamo l'ID
            return result[0]
            
        except Exception as e:
            print(f"Error fetching user ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user ID."
            )
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """
        Recupera un utente dal database tramite ID.
        
        Args:
            db: Sessione SQLAlchemy
            user_id: UUID dell'utente da cercare
        
        Returns:
            Optional[User]: Oggetto User ORM se trovato, None altrimenti
        
        Raises:
            HTTPException 500: In caso di errore durante la query
        """
        try:
            user = db.query(User).filter(User.id == user_id).first()
            return user
            
        except Exception as e:
            print(f"Error fetching user by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user information."
            )
