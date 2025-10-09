"""
Modelli Pydantic (schemi dati) per validazione input/output API.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Schema per il token JWT restituito dopo il login."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema per i dati contenuti nel JWT (il 'sub' è il name_user)."""
    username: Optional[str] = None


class UserBase(BaseModel):
    """Schema di base per l'utente (usato per login/registrazione)."""
    name_user: str = Field(..., description="Nome utente unico (usato come Subject JWT)")


class UserCreate(UserBase):
    """Schema per la registrazione."""
    password: str


class TaskBase(BaseModel):
    """Schema di base per l'attività."""
    description: str = Field(..., min_length=1, max_length=255)
    date_time: datetime
    completed: bool = False


class TaskCreate(TaskBase):
    """Schema per la creazione di una nuova attività."""
    pass  # Nessun tenant_id in input: il backend lo imposta!


class Task(TaskBase):
    """Schema completo dell'attività (inclusi gli ID di sistema)."""
    id: UUID
    tenant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


