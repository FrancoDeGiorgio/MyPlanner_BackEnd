"""
Service Layer per le task (Tasks) - SQLAlchemy ORM.

Contiene la business logic per la gestione delle task.
Coordina le operazioni tra Repository, User lookup e validazioni,
orchestrando il flusso di creazione/modifica/eliminazione delle task.
"""
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

# Import aggiornati per SQLAlchemy
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.utils.sanitizer import sanitize_html
from app.models.task import Task


class TaskService:
    """
    Service che gestisce la logica di business per le task.
    
    Responsabilità:
    - Coordinare repository per task e user
    - Validare business rules (es. tenant_id valido)
    - Gestire errori di business logic (task non trovata, permessi negati)
    
    IMPORTANTE: Il service NON conosce i dettagli SQL o RLS.
    Delega tutto l'accesso ai dati ai repository.
    Con SQLAlchemy ORM, i repository restituiscono direttamente oggetti Task
    che vengono serializzati automaticamente da Pydantic.
    """
    
    def __init__(self):
        """
        Inizializza il service con istanze dei repository necessari.
        
        TaskRepository: per operazioni CRUD sulle task
        UserRepository: per recuperare tenant_id degli utenti
        """
        self.task_repo = TaskRepository()
        self.user_repo = UserRepository()
    
    def list_tasks(self, db: Session, username: str) -> List[Task]:
        """
        Recupera tutte le task dell'utente autenticato.
        
        Processo:
        1. Chiama il repository per ottenere le task (con RLS attivo)
        2. Restituisce direttamente la lista di oggetti Task ORM
        3. Pydantic si occupa della serializzazione automatica
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente autenticato
        
        Returns:
            List[Task]: Lista di task ORM dell'utente (vuota se nessuna task)
        
        Note:
            - L'RLS garantisce che solo le task dell'utente siano visibili
            - Con ORM non serve più mappare dict → Pydantic
        """
        # Recupera le task dal repository (già filtrate da RLS)
        tasks = self.task_repo.get_all_tasks(db, username)
        
        return tasks
    
    def create_task(
        self,
        db: Session,
        username: str,
        title: str,
        description: str,
        color: str,
        date_time,
        end_time,
        duration_minutes,
        completed: bool
    ) -> Task:
        """
        Crea una nuova task per l'utente autenticato.
        
        Processo:
        1. Recupera il tenant_id (UUID utente) dal database
        2. Valida che l'utente esista
        3. Chiama il repository per creare la task con RLS
        4. Restituisce l'oggetto Task ORM creato
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente autenticato
            title: Titolo della task
            description: Descrizione della task
            color: Colore della task
            date_time: Data/ora inizio
            end_time: Data/ora fine (opzionale)
            duration_minutes: Durata in minuti (opzionale)
            completed: Flag completamento
        
        Returns:
            Task: Oggetto Task ORM con i dati della task creata (incluso ID)
        
        Raises:
            HTTPException 404: Se l'utente non esiste nel sistema
            HTTPException 400: Se l'RLS blocca la creazione (tenant_id non valido)
            HTTPException 500: Per altri errori durante la creazione
        
        Note:
            - Il tenant_id viene determinato automaticamente dall'username
            - L'utente NON può specificare un tenant_id diverso dal proprio
            - Validazioni Pydantic (end_time vs duration_minutes) già applicate dal router
        """
        # STEP 1: Recupera il tenant_id dell'utente autenticato
        tenant_id = self.user_repo.get_user_id_by_username(db, username)
        
        # STEP 2: Valida che l'utente esista
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found in the system. Cannot create task."
            )
        
        # STEP 3: Sanitizza la description HTML per prevenire XSS
        sanitized_description = sanitize_html(description)
        
        # STEP 4: Chiama il repository per creare la task
        task = self.task_repo.create_task(
            db=db,
            username=username,
            tenant_id=tenant_id,
            title=title,
            description=sanitized_description,
            color=color,
            date_time=date_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            completed=completed
        )
        
        # STEP 4: Restituisce l'oggetto Task ORM (Pydantic lo serializza automaticamente)
        return task
    
    def update_task(
        self,
        db: Session,
        username: str,
        task_id: UUID,
        title: str,
        description: str,
        color: str,
        date_time,
        end_time,
        duration_minutes,
        completed: bool
    ) -> Task:
        """
        Aggiorna una task esistente.
        
        Processo:
        1. Chiama il repository per aggiornare la task (con RLS)
        2. Verifica che la task esista e sia accessibile
        3. Restituisce l'oggetto Task ORM aggiornato
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente autenticato
            task_id: UUID della task da aggiornare
            title: Nuovo titolo
            description: Nuova descrizione
            color: Nuovo colore
            date_time: Nuova data/ora di inizio
            end_time: Nuova data/ora di fine (opzionale)
            duration_minutes: Nuova durata (opzionale)
            completed: Nuovo stato di completamento
        
        Returns:
            Task: Oggetto Task ORM con i dati aggiornati
        
        Raises:
            HTTPException 404: Se la task non esiste o non appartiene all'utente
            HTTPException 500: Per altri errori durante l'aggiornamento
        
        Note:
            - L'RLS garantisce che l'utente possa modificare solo le proprie task
            - Il tenant_id NON viene modificato (per sicurezza)
            - Validazioni Pydantic già applicate dal router
        """
        # STEP 1: Sanitizza la description HTML per prevenire XSS
        sanitized_description = sanitize_html(description)
        
        # STEP 2: Chiama il repository per aggiornare
        task = self.task_repo.update_task(
            db=db,
            username=username,
            task_id=task_id,
            title=title,
            description=sanitized_description,
            color=color,
            date_time=date_time,
            end_time=end_time,
            duration_minutes=duration_minutes,
            completed=completed
        )
        
        # STEP 3: Verifica che l'update sia riuscito
        if task is None:
            # La task non esiste o l'RLS ha bloccato l'accesso
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found or you do not have permission to update it."
            )
        
        # STEP 4: Restituisce l'oggetto Task ORM aggiornato
        return task
    
    def delete_task(
        self,
        db: Session,
        username: str,
        task_id: UUID
    ) -> None:
        """
        Elimina una task.
        
        Processo:
        1. Chiama il repository per eliminare la task (con RLS)
        2. Verifica che l'eliminazione sia riuscita
        3. Solleva 404 se la task non esiste o non è accessibile
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente autenticato
            task_id: UUID della task da eliminare
        
        Returns:
            None: L'endpoint restituisce 204 No Content in caso di successo
        
        Raises:
            HTTPException 404: Se la task non esiste o non appartiene all'utente
            HTTPException 500: Per altri errori durante l'eliminazione
        
        Note:
            - L'RLS garantisce che l'utente possa eliminare solo le proprie task
            - Non c'è "soft delete", la task viene rimossa dal database
        """
        # STEP 1: Chiama il repository per eliminare
        deleted = self.task_repo.delete_task(db, username, task_id)
        
        # STEP 2: Verifica che la delete sia riuscita
        if not deleted:
            # La task non esiste o l'RLS ha bloccato l'accesso
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found or you do not have permission to delete it."
            )
        
        # Nessun return: l'endpoint restituirà 204 No Content
    
    def get_task(
        self,
        db: Session,
        username: str,
        task_id: UUID
    ) -> Task:
        """
        Recupera una singola task per ID.
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente autenticato
            task_id: UUID della task da recuperare
        
        Returns:
            Task: Oggetto Task ORM se trovato e accessibile
        
        Raises:
            HTTPException 404: Se la task non esiste o non appartiene all'utente
        """
        task = self.task_repo.get_task_by_id(db, username, task_id)
        
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found or you do not have permission to access it."
            )
        
        return task
