"""
Repository Layer per le task (Tasks) - SQLAlchemy ORM.

Responsabile dell'accesso ai dati per la tabella 'tasks'.
Tutte le operazioni includono automaticamente il contesto RLS tramite
l'event listener configurato in database.py.
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.task import Task
from app.core.database import set_rls_context


class TaskRepository:
    """
    Repository per la gestione delle task nel database con SQLAlchemy ORM.
    
    Tutti i metodi che accedono alla tabella 'tasks' configurano
    automaticamente il contesto RLS tramite l'event listener.
    Il contesto RLS garantisce che:
    1. Le policy RLS siano attive (ruolo 'authenticated')
    2. Il contesto JWT sia configurato correttamente
    3. L'utente possa accedere SOLO alle proprie task
    
    IMPORTANTE: La sicurezza multi-tenant è garantita a livello database
    tramite RLS, applicato automaticamente dall'event listener SQLAlchemy.
    """
    
    def get_all_tasks(self, db: Session, username: str) -> List[Task]:
        """
        Recupera tutte le task dell'utente autenticato.
        
        Grazie all'RLS (configurato dall'event listener), questa query
        SELECT restituisce SOLO le task dove tenant_id corrisponde
        all'ID dell'utente autenticato.
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente autenticato (per contesto RLS)
        
        Returns:
            List[Task]: Lista di oggetti Task ORM dell'utente
        
        Note:
            - L'event listener configura automaticamente il contesto RLS
            - Le task sono ordinate per date_time discendente (più recenti prima)
            - Restituisce lista vuota se l'utente non ha task
        """
        try:
            # Configura il contesto RLS per questa sessione
            set_rls_context(db, username)
            
            # Query ORM - l'RLS filtra automaticamente per tenant_id
            tasks = db.query(Task).order_by(Task.date_time.desc()).all()
            
            return tasks
            
        except Exception as e:
            print(f"Error fetching tasks: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve tasks."
            )
    
    def create_task(
        self,
        db: Session,
        username: str,
        tenant_id: UUID,
        title: str,
        description: str,
        color: str,
        date_time: datetime,
        end_time: Optional[datetime],
        duration_minutes: Optional[int],
        completed: bool
    ) -> Task:
        """
        Crea una nuova task nel database.
        
        L'RLS verifica che il tenant_id fornito corrisponda all'utente
        autenticato (policy INSERT WITH CHECK). Se non corrisponde,
        l'INSERT fallisce.
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente autenticato (per contesto RLS)
            tenant_id: UUID del tenant (deve corrispondere all'utente autenticato!)
            title: Titolo della task
            description: Descrizione della task
            color: Colore della task (green, purple, orange, cyan, pink, yellow)
            date_time: Data/ora di inizio della task
            end_time: Data/ora di fine (opzionale)
            duration_minutes: Durata in minuti (opzionale)
            completed: Flag di completamento
        
        Returns:
            Task: Oggetto Task ORM creato con ID generato
        
        Raises:
            HTTPException 400: Se l'RLS blocca l'inserimento (tenant_id non valido)
            HTTPException 500: Per altri errori database
        
        Note:
            - Il contesto RLS viene configurato automaticamente
            - L'ID e created_at vengono generati automaticamente dal database
            - updated_at viene gestito dal trigger PostgreSQL
        """
        try:
            # Configura il contesto RLS per questa sessione
            set_rls_context(db, username)
            
            # Crea nuova istanza del modello Task
            new_task = Task(
                tenant_id=tenant_id,
                title=title,
                description=description,
                color=color,
                date_time=date_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                completed=completed
            )
            
            # Aggiungi alla sessione
            db.add(new_task)
            
            # Commit per persistere nel database
            db.commit()
            
            # Refresh per ottenere i valori generati dal database
            db.refresh(new_task)
            
            return new_task
            
        except IntegrityError as e:
            # Violazione di constraint (FK, CHECK, ecc.)
            db.rollback()
            
            # Se è un problema di RLS/tenant_id, solleva 400
            if 'tenant_id' in str(e.orig) or 'fkey' in str(e.orig).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Task creation failed. Invalid tenant_id or RLS violation."
                )
            
            # Altro tipo di constraint violation
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task creation failed due to constraint violation."
            )
            
        except Exception as e:
            db.rollback()
            print(f"Error creating task: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create task."
            )
    
    def update_task(
        self,
        db: Session,
        username: str,
        task_id: UUID,
        title: str,
        description: str,
        color: str,
        date_time: datetime,
        end_time: Optional[datetime],
        duration_minutes: Optional[int],
        completed: bool
    ) -> Optional[Task]:
        """
        Aggiorna una task esistente.
        
        L'RLS garantisce che l'UPDATE possa modificare SOLO task
        appartenenti all'utente autenticato (policy UPDATE USING + WITH CHECK).
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente autenticato (per contesto RLS)
            task_id: UUID della task da aggiornare
            title: Nuovo titolo
            description: Nuova descrizione
            color: Nuovo colore
            date_time: Nuova data/ora di inizio
            end_time: Nuova data/ora di fine (opzionale)
            duration_minutes: Nuova durata (opzionale)
            completed: Nuovo stato di completamento
        
        Returns:
            Optional[Task]: Oggetto Task ORM aggiornato se successo, None se task non trovata
        
        Note:
            - Se l'RLS blocca l'UPDATE, la query non troverà la task
            - Non modifichiamo tenant_id per sicurezza
            - updated_at viene aggiornato automaticamente dal trigger
        """
        try:
            # Configura il contesto RLS per questa sessione
            set_rls_context(db, username)
            
            # Query per trovare la task (filtrata da RLS)
            task = db.query(Task).filter(Task.id == task_id).first()
            
            if task is None:
                # Task non trovata o non appartiene all'utente (RLS block)
                return None
            
            # Aggiorna i campi
            task.title = title
            task.description = description
            task.color = color
            task.date_time = date_time
            task.end_time = end_time
            task.duration_minutes = duration_minutes
            task.completed = completed
            
            # Commit per persistere le modifiche
            db.commit()
            
            # Refresh per ottenere updated_at aggiornato dal trigger
            db.refresh(task)
            
            return task
            
        except Exception as e:
            db.rollback()
            print(f"Error updating task: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update task."
            )
    
    def delete_task(
        self,
        db: Session,
        username: str,
        task_id: UUID
    ) -> bool:
        """
        Elimina una task dal database.
        
        L'RLS garantisce che il DELETE possa rimuovere SOLO task
        appartenenti all'utente autenticato (policy DELETE USING).
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente autenticato (per contesto RLS)
            task_id: UUID della task da eliminare
        
        Returns:
            bool: True se la task è stata eliminata, False se non trovata o non accessibile
        
        Note:
            - Se l'RLS blocca il DELETE, la query non troverà la task
        """
        try:
            # Configura il contesto RLS per questa sessione
            set_rls_context(db, username)
            
            # Query per trovare la task (filtrata da RLS)
            task = db.query(Task).filter(Task.id == task_id).first()
            
            if task is None:
                # Task non trovata o non appartiene all'utente (RLS block)
                return False
            
            # Elimina la task
            db.delete(task)
            
            # Commit per persistere l'eliminazione
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error deleting task: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete task."
            )
    
    def get_task_by_id(
        self,
        db: Session,
        username: str,
        task_id: UUID
    ) -> Optional[Task]:
        """
        Recupera una singola task per ID.
        
        L'RLS garantisce che venga restituita SOLO se appartiene all'utente.
        
        Args:
            db: Sessione SQLAlchemy
            username: Username dell'utente autenticato (per contesto RLS)
            task_id: UUID della task da recuperare
        
        Returns:
            Optional[Task]: Oggetto Task ORM se trovato e accessibile, None altrimenti
        """
        try:
            # Configura il contesto RLS per questa sessione
            set_rls_context(db, username)
            
            # Query per trovare la task (filtrata da RLS)
            task = db.query(Task).filter(Task.id == task_id).first()
            
            return task
            
        except Exception as e:
            print(f"Error fetching task by ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve task."
            )
