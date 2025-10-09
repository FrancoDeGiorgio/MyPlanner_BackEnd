"""
Endpoint CRUD per le attività (tasks), protetti da RLS.
"""
from typing import List
from uuid import UUID

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db_conn, execute_protected_query, get_user_id_by_username
from dependencies import get_current_user
from schemas import Task, TaskCreate, TaskBase


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=List[Task], summary="Recupera tutte le attività del tenant")
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


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED, summary="Crea una nuova attività")
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
    params = (str(tenant_id), task.description, task.date_time, task.completed)
    
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


@router.put("/{task_id}", response_model=Task, summary="Aggiorna un'attività esistente")
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
    params = (task_update.description, task_update.date_time, task_update.completed, str(task_id))

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


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Elimina un'attività")
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
    params = (str(task_id),)

    # Esegue la query, impostando il contesto RLS
    result = execute_protected_query(conn, username, sql_query, params, fetch_one=True)

    if not result:
        # Se la riga non viene restituita, o l'ID non esiste, o l'utente non è il proprietario (RLS)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found or you do not have permission to delete it (RLS block)."
        )

    return

