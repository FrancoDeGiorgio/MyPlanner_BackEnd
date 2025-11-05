"""
Service Layer per il dominio Tasks.

Contiene la business logic per la gestione delle task.
Coordina le operazioni tra Repository, User lookup e validazioni,
orchestrando il flusso di creazione/modifica/eliminazione delle task.
"""
from typing import List
from uuid import UUID
import psycopg2
from fastapi import HTTPException, status

from domains.tasks.repository import TaskRepository
from domains.auth.repository import UserRepository
from domains.tasks.schemas import Task, TaskCreate, TaskBase


class TaskService:
    """
    Service che gestisce la logica di business per le task.
    
    Responsabilità:
    - Coordinare repository per task e user
    - Validare business rules (es. tenant_id valido)
    - Mappare tra dict (repository) e Pydantic models (API)
    - Gestire errori di business logic (task non trovata, permessi negati)
    
    IMPORTANTE: Il service NON conosce i dettagli SQL o RLS.
    Delega tutto l'accesso ai dati ai repository.
    """
    
    def __init__(self):
        """
        Inizializza il service con istanze dei repository necessari.
        
        TaskRepository: per operazioni CRUD sulle task
        UserRepository: per recuperare tenant_id degli utenti
        """
        self.task_repo = TaskRepository()
        self.user_repo = UserRepository()
    
    def list_tasks(self, conn: psycopg2.connect, username: str) -> List[Task]:
        """
        Recupera tutte le task dell'utente autenticato.
        
        Processo:
        1. Chiama il repository per ottenere le task (con RLS attivo)
        2. Mappa ogni dict risultato su un oggetto Pydantic Task
        3. Restituisce la lista di Task per serializzazione JSON
        
        Args:
            conn: Connessione al database
            username: Username dell'utente autenticato
        
        Returns:
            List[Task]: Lista di task dell'utente (vuota se nessuna task)
        
        Note:
            - L'RLS garantisce che solo le task dell'utente siano visibili
            - Errori di mapping vengono loggati ma non bloccano le altre task
        """
        # STEP 1: Recupera i dati raw dal repository
        task_dicts = self.task_repo.get_all_tasks(conn, username)
        
        # STEP 2: Mappa ogni dict su un oggetto Pydantic Task
        tasks = []
        for task_dict in task_dicts:
            try:
                # Converti eventuali stringhe UUID in oggetti UUID
                task = Task(
                    id=UUID(task_dict['id']) if isinstance(task_dict['id'], str) else task_dict['id'],
                    tenant_id=UUID(task_dict['tenant_id']) if isinstance(task_dict['tenant_id'], str) else task_dict['tenant_id'],
                    title=task_dict['title'],
                    description=task_dict['description'],
                    color=task_dict['color'],
                    date_time=task_dict['date_time'],
                    end_time=task_dict['end_time'],
                    duration_minutes=task_dict['duration_minutes'],
                    completed=task_dict['completed'],
                    created_at=task_dict['created_at']
                )
                tasks.append(task)
            except Exception as e:
                # Log l'errore ma continua con le altre task
                print(f"Error mapping task {task_dict.get('id', 'unknown')}: {e}")
                # In produzione, potresti voler usare un logger appropriato
        
        return tasks
    
    def create_task(
        self,
        conn: psycopg2.connect,
        username: str,
        task_create: TaskCreate
    ) -> Task:
        """
        Crea una nuova task per l'utente autenticato.
        
        Processo:
        1. Recupera il tenant_id (UUID utente) dal database
        2. Valida che l'utente esista
        3. Chiama il repository per creare la task con RLS
        4. Mappa il risultato su un oggetto Pydantic Task
        
        Args:
            conn: Connessione al database
            username: Username dell'utente autenticato
            task_create: DTO Pydantic con i dati della task da creare
        
        Returns:
            Task: Oggetto Pydantic con i dati della task creata (incluso ID)
        
        Raises:
            HTTPException 404: Se l'utente non esiste nel sistema
            HTTPException 400: Se l'RLS blocca la creazione (tenant_id non valido)
            HTTPException 500: Per altri errori durante la creazione
        
        Note:
            - Il tenant_id viene determinato automaticamente dall'username
            - L'utente NON può specificare un tenant_id diverso dal proprio
            - Validazioni Pydantic (end_time vs duration_minutes) già applicate
        """
        # STEP 1: Recupera il tenant_id dell'utente autenticato
        tenant_id = self.user_repo.get_user_id_by_username(conn, username)
        
        # STEP 2: Valida che l'utente esista
        if tenant_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User '{username}' not found in the system. Cannot create task."
            )
        
        # STEP 3: Chiama il repository per creare la task
        task_dict = self.task_repo.create_task(
            conn=conn,
            username=username,
            tenant_id=tenant_id,
            title=task_create.title,
            description=task_create.description,
            color=task_create.color,
            date_time=task_create.date_time,
            end_time=task_create.end_time,
            duration_minutes=task_create.duration_minutes,
            completed=task_create.completed
        )
        
        # STEP 4: Mappa il risultato su un oggetto Pydantic Task
        task = Task(
            id=UUID(task_dict['id']) if isinstance(task_dict['id'], str) else task_dict['id'],
            tenant_id=UUID(task_dict['tenant_id']) if isinstance(task_dict['tenant_id'], str) else task_dict['tenant_id'],
            title=task_dict['title'],
            description=task_dict['description'],
            color=task_dict['color'],
            date_time=task_dict['date_time'],
            end_time=task_dict['end_time'],
            duration_minutes=task_dict['duration_minutes'],
            completed=task_dict['completed'],
            created_at=task_dict['created_at']
        )
        
        return task
    
    def update_task(
        self,
        conn: psycopg2.connect,
        username: str,
        task_id: UUID,
        task_update: TaskBase
    ) -> Task:
        """
        Aggiorna una task esistente.
        
        Processo:
        1. Chiama il repository per aggiornare la task (con RLS)
        2. Verifica che la task esista e sia accessibile
        3. Mappa il risultato su un oggetto Pydantic Task
        
        Args:
            conn: Connessione al database
            username: Username dell'utente autenticato
            task_id: UUID della task da aggiornare
            task_update: DTO Pydantic con i nuovi dati della task
        
        Returns:
            Task: Oggetto Pydantic con i dati aggiornati della task
        
        Raises:
            HTTPException 404: Se la task non esiste o non appartiene all'utente
            HTTPException 500: Per altri errori durante l'aggiornamento
        
        Note:
            - L'RLS garantisce che l'utente possa modificare solo le proprie task
            - Il tenant_id NON viene modificato (per sicurezza)
            - Validazioni Pydantic già applicate sul task_update
        """
        # STEP 1: Chiama il repository per aggiornare
        task_dict = self.task_repo.update_task(
            conn=conn,
            username=username,
            task_id=task_id,
            title=task_update.title,
            description=task_update.description,
            color=task_update.color,
            date_time=task_update.date_time,
            end_time=task_update.end_time,
            duration_minutes=task_update.duration_minutes,
            completed=task_update.completed
        )
        
        # STEP 2: Verifica che l'update sia riuscito
        if task_dict is None:
            # La task non esiste o l'RLS ha bloccato l'accesso
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found or you do not have permission to update it."
            )
        
        # STEP 3: Mappa il risultato su un oggetto Pydantic Task
        task = Task(
            id=UUID(task_dict['id']) if isinstance(task_dict['id'], str) else task_dict['id'],
            tenant_id=UUID(task_dict['tenant_id']) if isinstance(task_dict['tenant_id'], str) else task_dict['tenant_id'],
            title=task_dict['title'],
            description=task_dict['description'],
            color=task_dict['color'],
            date_time=task_dict['date_time'],
            end_time=task_dict['end_time'],
            duration_minutes=task_dict['duration_minutes'],
            completed=task_dict['completed'],
            created_at=task_dict['created_at']
        )
        
        return task
    
    def delete_task(
        self,
        conn: psycopg2.connect,
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
            conn: Connessione al database
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
        deleted = self.task_repo.delete_task(conn, username, task_id)
        
        # STEP 2: Verifica che la delete sia riuscita
        if not deleted:
            # La task non esiste o l'RLS ha bloccato l'accesso
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found or you do not have permission to delete it."
            )
        
        # Nessun return: l'endpoint restituirà 204 No Content

