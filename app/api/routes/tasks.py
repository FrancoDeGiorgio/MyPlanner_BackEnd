"""
API Router per task (Tasks) - API Layer / Presentation Layer.

Definisce gli endpoint REST per operazioni CRUD sulle task.
Il router è responsabile SOLO di:
- Ricevere richieste HTTP
- Validare input tramite Pydantic schemas
- Delegare la business logic al Service Layer
- Restituire risposte HTTP formattate

NON contiene business logic o accesso diretto al database.
"""
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status

# Import aggiornati per la nuova architettura
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.api.middleware.rate_limit import get_global_rate_limit
from app.schemas.task import Task, TaskCreate, TaskBase
from app.services.task_service import TaskService


# --- INIZIALIZZAZIONE ROUTER ---
# Prefix: tutti gli endpoint di questo router inizieranno con /tasks
# Tags: raggruppamento nella documentazione OpenAPI
router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)

# --- INIZIALIZZAZIONE SERVICE ---
# Il service contiene la business logic ed è usato da tutti gli endpoint
task_service = TaskService()


@router.get(
    "",
    response_model=List[Task],
    summary="Recupera tutte le task dell'utente autenticato",
    dependencies=[Depends(get_global_rate_limit())]  # Applica rate limit globale: 100 req/min
)
def read_tasks(
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint per recuperare tutte le task dell'utente corrente.
    
    Grazie alla Row-Level Security (RLS), vengono restituite SOLO
    le task dove tenant_id corrisponde all'utente autenticato.
    
    Process:
    1. Estrae username dal JWT token (dependency get_current_user)
    2. Delega al service il recupero delle task
    3. Restituisce la lista di task (vuota se nessuna task presente)
    
    Args:
        username: Username estratto dal JWT (injected by dependency)
        db: Sessione SQLAlchemy (injected by dependency)
    
    Returns:
        List[Task]: Lista di task dell'utente, ordinate per date_time DESC
    
    Raises:
        HTTPException 401: Se il token JWT è invalido o mancante
        HTTPException 500: Per errori interni del server
    
    Example Request:
        GET /tasks
        Authorization: Bearer <token>
    
    Example Response:
        HTTP 200 OK
        
        [
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "title": "Riunione team",
                "description": "Discutere sprint planning",
                "color": "purple",
                "date_time": "2025-11-05T14:00:00",
                "end_time": null,
                "duration_minutes": 60,
                "completed": false,
                "created_at": "2025-11-05T10:30:00"
            }
        ]
    
    Note:
        - L'RLS garantisce isolamento completo tra tenant
        - Nessun parametro di filtro necessario: l'username è dal token
        - Le task sono automaticamente ordinate per data/ora
    """
    # Delega tutto il lavoro al service
    # Il router è solo un bridge tra HTTP e business logic
    tasks = task_service.list_tasks(db, username)
    return tasks


@router.post(
    "",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    summary="Crea una nuova task"
)
def create_task(
    task: TaskCreate,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint per creare una nuova task per l'utente autenticato.
    
    Il tenant_id viene determinato automaticamente dal backend
    in base all'utente autenticato (estratto dal JWT token).
    
    Process:
    1. Valida i dati in input tramite Pydantic (TaskCreate schema)
    2. Estrae username dal JWT token
    3. Delega al service la creazione (che recupera tenant_id e salva)
    4. Restituisce la task creata con ID e timestamp
    
    Args:
        task: Schema Pydantic con i dati della task (NO tenant_id!)
        username: Username estratto dal JWT (injected by dependency)
        db: Sessione SQLAlchemy (injected by dependency)
    
    Returns:
        Task: Task creata con tutti i campi popolati (inclusi id, tenant_id, created_at)
    
    Raises:
        HTTPException 401: Se il token JWT è invalido o mancante
        HTTPException 404: Se l'utente non esiste nel sistema
        HTTPException 422: Se i dati di input non sono validi (Pydantic)
        HTTPException 500: Per errori interni del server
    
    Example Request:
        POST /tasks
        Authorization: Bearer <token>
        Content-Type: application/json
        
        {
            "title": "Riunione team",
            "description": "Discutere sprint planning",
            "color": "purple",
            "date_time": "2025-11-05T14:00:00",
            "duration_minutes": 60,
            "completed": false
        }
    
    Example Response:
        HTTP 201 Created
        
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "title": "Riunione team",
            "description": "Discutere sprint planning",
            "color": "purple",
            "date_time": "2025-11-05T14:00:00",
            "end_time": null,
            "duration_minutes": 60,
            "completed": false,
            "created_at": "2025-11-05T10:30:00"
        }
    
    Security:
        - Il tenant_id NON può essere specificato dall'utente (security by design)
        - Viene ricavato automaticamente dal JWT token
        - L'RLS valida che tenant_id corrisponda all'utente autenticato
    """
    # Delega tutta la logica al service
    created_task = task_service.create_task(
        db=db,
        username=username,
        title=task.title,
        description=task.description,
        color=task.color,
        date_time=task.date_time,
        end_time=task.end_time,
        duration_minutes=task.duration_minutes,
        completed=task.completed
    )
    return created_task


@router.put(
    "/{task_id}",
    response_model=Task,
    summary="Aggiorna una task esistente",
    dependencies=[Depends(get_global_rate_limit())]  # Applica rate limit globale: 100 req/min
)
def update_task(
    task_id: UUID,
    task_update: TaskBase,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint per aggiornare una task esistente.
    
    L'utente può modificare SOLO le proprie task. L'RLS garantisce
    che task di altri tenant non siano accessibili.
    
    Process:
    1. Valida i dati in input tramite Pydantic (TaskBase schema)
    2. Estrae username dal JWT token
    3. Delega al service l'aggiornamento (che verifica ownership via RLS)
    4. Restituisce la task aggiornata
    
    Args:
        task_id: UUID della task da aggiornare (path parameter)
        task_update: Schema Pydantic con i nuovi dati della task
        username: Username estratto dal JWT (injected by dependency)
        db: Sessione SQLAlchemy (injected by dependency)
    
    Returns:
        Task: Task aggiornata con tutti i campi
    
    Raises:
        HTTPException 401: Se il token JWT è invalido o mancante
        HTTPException 404: Se la task non esiste o non appartiene all'utente
        HTTPException 422: Se i dati di input non sono validi (Pydantic)
        HTTPException 500: Per errori interni del server
    
    Example Request:
        PUT /tasks/550e8400-e29b-41d4-a716-446655440000
        Authorization: Bearer <token>
        Content-Type: application/json
        
        {
            "title": "Riunione team (AGGIORNATO)",
            "description": "Discutere sprint planning e retrospettiva",
            "color": "orange",
            "date_time": "2025-11-05T15:00:00",
            "duration_minutes": 90,
            "completed": true
        }
    
    Example Response:
        HTTP 200 OK
        
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "tenant_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
            "title": "Riunione team (AGGIORNATO)",
            "description": "Discutere sprint planning e retrospettiva",
            "color": "orange",
            "date_time": "2025-11-05T15:00:00",
            "end_time": null,
            "duration_minutes": 90,
            "completed": true,
            "created_at": "2025-11-05T10:30:00"
        }
    
    Note:
        - Il tenant_id NON viene modificato (per sicurezza)
        - L'id e created_at sono immutabili
        - L'RLS impedisce di modificare task di altri utenti (restituisce 404)
    """
    # Delega tutta la logica al service
    updated_task = task_service.update_task(
        db=db,
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
    return updated_task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Elimina una task",
    dependencies=[Depends(get_global_rate_limit())]  # Applica rate limit globale: 100 req/min
)
def delete_task(
    task_id: UUID,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint per eliminare una task.
    
    L'utente può eliminare SOLO le proprie task. L'RLS garantisce
    che task di altri tenant non siano accessibili.
    
    Process:
    1. Estrae username dal JWT token
    2. Delega al service l'eliminazione (che verifica ownership via RLS)
    3. Restituisce 204 No Content in caso di successo
    
    Args:
        task_id: UUID della task da eliminare (path parameter)
        username: Username estratto dal JWT (injected by dependency)
        db: Sessione SQLAlchemy (injected by dependency)
    
    Returns:
        None: HTTP 204 No Content (success without body)
    
    Raises:
        HTTPException 401: Se il token JWT è invalido o mancante
        HTTPException 404: Se la task non esiste o non appartiene all'utente
        HTTPException 500: Per errori interni del server
    
    Example Request:
        DELETE /tasks/550e8400-e29b-41d4-a716-446655440000
        Authorization: Bearer <token>
    
    Example Response:
        HTTP 204 No Content
        (nessun body)
    
    Note:
        - L'eliminazione è permanente (hard delete, no soft delete)
        - L'RLS impedisce di eliminare task di altri utenti (restituisce 404)
        - 204 No Content è lo status code standard per DELETE di successo
    """
    # Delega tutta la logica al service
    task_service.delete_task(db, username, task_id)
    # Nessun return: FastAPI restituirà automaticamente 204 No Content

