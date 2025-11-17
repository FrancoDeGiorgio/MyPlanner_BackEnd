"""
Domain Model per User - SQLAlchemy ORM.

Definisce l'entità User come modello SQLAlchemy ORM.
Questo modello rappresenta sia l'entità di business che il mapping
sulla tabella 'users' del database.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    Entità di dominio e modello ORM che rappresenta un utente/tenant del sistema.
    
    Questo modello SQLAlchemy:
    - Mappa sulla tabella 'users' nel database
    - Rappresenta l'entità di business User
    - Gestisce le relazioni con altre entità (Task)
    
    Attributes:
        id: Identificatore univoco UUID dell'utente
        name_user: Username univoco, usato anche come tenant identifier per RLS
        hashed_password: Password hashata con bcrypt (mai password in chiaro!)
        created_at: Timestamp di creazione dell'account
        tasks: Relationship con le task dell'utente (lazy loaded)
    
    Relationships:
        tasks: Lista di Task appartenenti all'utente
               - back_populates="owner": riferimento bidirezionale
               - cascade="all, delete-orphan": elimina task quando si elimina user
    
    Note:
        - L'ID viene generato automaticamente dal database con gen_random_uuid()
        - created_at viene popolato automaticamente con CURRENT_TIMESTAMP
        - La tabella 'users' NON ha policy RLS attive
    """
    __tablename__ = 'users'
    
    # --- COLONNE ---
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        nullable=False,
        comment="Identificatore univoco utente (tenant_id per RLS)"
    )
    
    name_user = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Username univoco per login"
    )
    
    hashed_password = Column(
        Text,
        nullable=False,
        comment="Password hashata con bcrypt"
    )
    
    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Timestamp registrazione"
    )
    
    # --- RELATIONSHIPS ---
    tasks = relationship(
        "Task",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    settings = relationship(
        "UserSettings",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,  # Relazione 1:1
        lazy="select"
    )
    
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        """
        Rappresentazione string-safe dell'utente (senza password).
        
        IMPORTANTE: Non includere mai l'hashed_password nei log o repr!
        Anche se è hashata, è buona pratica non esporla mai.
        
        Returns:
            str: Rappresentazione leggibile dell'utente
        """
        return f"User(id={self.id}, name_user='{self.name_user}', created_at={self.created_at})"
    
    def __str__(self) -> str:
        """String representation per display user-friendly."""
        return f"{self.name_user}"
