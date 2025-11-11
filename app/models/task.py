"""
Domain Model per Task - SQLAlchemy ORM.

Definisce l'entità Task come modello SQLAlchemy ORM con business logic.
Questo modello rappresenta sia l'entità di business che il mapping
sulla tabella 'tasks' del database.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, TIMESTAMP, Integer, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Task(Base):
    """
    Entità di dominio e modello ORM che rappresenta una task/attività.
    
    Questo modello SQLAlchemy:
    - Mappa sulla tabella 'tasks' nel database
    - Rappresenta l'entità di business Task
    - Include business logic (get_effective_duration, is_overdue)
    - È protetto da Row-Level Security (RLS)
    
    Attributes:
        id: Identificatore univoco UUID della task
        tenant_id: UUID del tenant (utente) proprietario della task
        title: Titolo breve della task (max 200 caratteri)
        description: Descrizione dettagliata della task
        color: Colore associato per categorizzazione visiva
        date_time: Data/ora di inizio della task
        end_time: Data/ora di fine (opzionale, mutualmente esclusivo con duration_minutes)
        duration_minutes: Durata in minuti (opzionale, mutualmente esclusivo con end_time)
        completed: Flag che indica se la task è completata
        created_at: Timestamp di creazione della task
        updated_at: Timestamp ultimo aggiornamento (aggiornato automaticamente da trigger)
        owner: Relationship con l'utente proprietario (lazy loaded)
    
    Business Rules:
        - end_time e duration_minutes sono mutuamente esclusivi
        - Se end_time è specificato, deve essere dopo date_time
        - duration_minutes deve essere >= 5 minuti
        - Le validazioni sono applicate anche a livello database (constraints)
    
    Relationships:
        owner: Riferimento all'utente proprietario (User)
               - back_populates="tasks": riferimento bidirezionale
    
    Note:
        - Protetto da Row-Level Security (RLS) in produzione
        - L'updated_at viene aggiornato automaticamente da trigger PostgreSQL
        - I metodi di business logic sono mantenuti dal vecchio modello dataclass
    """
    __tablename__ = 'tasks'
    
    # --- COLONNE ---
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        nullable=False,
        comment="Identificatore univoco task"
    )
    
    tenant_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Riferimento utente proprietario (per isolamento RLS)"
    )
    
    title = Column(
        String(200),
        nullable=False,
        comment="Titolo breve task (max 200 caratteri)"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Descrizione dettagliata task"
    )
    
    color = Column(
        String(20),
        server_default='green',
        nullable=False,
        comment="Colore per categorizzazione visiva (green, purple, orange, cyan, pink, yellow)"
    )
    
    date_time = Column(
        TIMESTAMP,
        nullable=False,
        index=True,
        comment="Data/ora inizio task"
    )
    
    end_time = Column(
        TIMESTAMP,
        nullable=True,
        comment="Data/ora fine task (opzionale, mutualmente esclusivo con duration_minutes)"
    )
    
    duration_minutes = Column(
        Integer,
        nullable=True,
        comment="Durata in minuti (5-1440, opzionale, mutualmente esclusivo con end_time)"
    )
    
    completed = Column(
        Boolean,
        server_default='false',
        nullable=False,
        index=True,
        comment="Flag completamento task"
    )
    
    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Timestamp creazione"
    )
    
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Timestamp ultimo aggiornamento"
    )
    
    # --- CONSTRAINTS ---
    __table_args__ = (
        CheckConstraint(
            'duration_minutes IS NULL OR duration_minutes >= 5',
            name='chk_duration'
        ),
        CheckConstraint(
            'end_time IS NULL OR end_time > date_time',
            name='chk_end_time'
        ),
    )
    
    # --- RELATIONSHIPS ---
    owner = relationship(
        "User",
        back_populates="tasks",
        lazy="select"
    )
    
    # --- BUSINESS LOGIC METHODS ---
    
    def get_effective_duration(self) -> Optional[int]:
        """
        Calcola la durata effettiva della task in minuti.
        
        Questo metodo implementa la business logic per determinare
        quanto dura una task, gestendo i due modi possibili di
        specificare la durata (duration_minutes o end_time).
        
        Returns:
            Optional[int]: Durata in minuti se disponibile, None altrimenti
        
        Note:
            - Se duration_minutes è specificato, lo restituisce direttamente
            - Se end_time è specificato, calcola la differenza in minuti
            - Se nessuno dei due, restituisce None
        
        Example:
            >>> task = Task(duration_minutes=60, end_time=None)
            >>> task.get_effective_duration()
            60
            
            >>> task2 = Task(
            ...     duration_minutes=None,
            ...     end_time=datetime(2025, 1, 1, 15, 0),
            ...     date_time=datetime(2025, 1, 1, 14, 0)
            ... )
            >>> task2.get_effective_duration()
            60
        """
        if self.duration_minutes is not None:
            return self.duration_minutes
        
        if self.end_time is not None and self.date_time is not None:
            delta = self.end_time - self.date_time
            return int(delta.total_seconds() / 60)
        
        return None
    
    def is_overdue(self, current_time: datetime) -> bool:
        """
        Verifica se la task è in ritardo rispetto al tempo corrente.
        
        Questo metodo implementa la business logic per determinare
        se una task è scaduta. Una task è considerata in ritardo se:
        - NON è completata E
        - La sua deadline (end_time o date_time) è passata
        
        Args:
            current_time: Timestamp corrente per il confronto
                         (passato come parametro per permettere testing
                         con date/ore arbitrarie)
        
        Returns:
            bool: True se la task è scaduta e non completata, False altrimenti
        
        Note:
            - Una task completata non è mai considerata in ritardo
            - La deadline è end_time se disponibile, altrimenti date_time
            - Se nessuna deadline, la task non può essere in ritardo
        
        Example:
            >>> from datetime import datetime, timedelta
            >>> now = datetime(2025, 1, 10, 12, 0)
            >>> 
            >>> task = Task(
            ...     date_time=datetime(2025, 1, 1, 10, 0),
            ...     completed=False
            ... )
            >>> task.is_overdue(now)
            True
            
            >>> task.completed = True
            >>> task.is_overdue(now)
            False  # Le task completate non sono in ritardo
        """
        if self.completed:
            # Una task completata non è mai in ritardo,
            # anche se completata dopo la deadline
            return False
        
        # Determina la deadline: preferisci end_time se disponibile
        deadline = self.end_time if self.end_time else self.date_time
        
        # Se non c'è nessuna deadline, non può essere in ritardo
        return deadline < current_time if deadline else False
    
    def __repr__(self) -> str:
        """
        Rappresentazione string della task per debug/logging.
        
        Include:
        - Stato di completamento (simbolo visivo)
        - Titolo della task
        - Data/ora di inizio
        - Tenant ID
        
        Returns:
            str: Rappresentazione leggibile della task
        
        Example:
            >>> print(task)
            Task(✓ Riunione team @ 2025-01-01 14:00:00, tenant=7c9e6679-7425-40de-944b-e07fc1f90ae7)
        """
        status = "✓" if self.completed else "○"
        return f"Task({status} {self.title} @ {self.date_time}, tenant={self.tenant_id})"
    
    def __str__(self) -> str:
        """String representation per display user-friendly."""
        return f"{self.title} ({self.date_time.strftime('%Y-%m-%d %H:%M') if self.date_time else 'No date'})"
