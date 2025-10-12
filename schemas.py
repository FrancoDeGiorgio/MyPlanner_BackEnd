"""
Modelli Pydantic (schemi dati) per validazione input/output API.
"""
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator


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

ColorLiteral = Literal["green", "purple", "orange", "cyan", "pink", "yellow"]

class TaskBase(BaseModel):
    """Schema di base per l'attività."""
    title: str = Field(..., min_length=1, max_length=150)
    description: str = Field(..., min_length=1, max_length=255)
    color: ColorLiteral = Field(default="green")
    date_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=5, le=1440)
    completed: bool = False

    @model_validator(mode="after")
    def check_time_constraints(self):
        if self.end_time and self.duration_minutes:
            raise ValueError("Puoi impostare solo end_time oppure duration_minutes, non entrambi.")
        if self.end_time and self.end_time <= self.date_time:
            raise ValueError("La data di fine deve essere successiva alla data di inizio.")
        return self


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


