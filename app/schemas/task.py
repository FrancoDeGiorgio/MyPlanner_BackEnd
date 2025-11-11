"""
Pydantic Schemas (DTO - Data Transfer Objects) per le task.

Questi schemi definiscono la struttura dei dati in ingresso e uscita
dalle API REST per le task, con validazione automatica tramite Pydantic.

IMPORTANTE: Separazione tra Models e Schemas
---------------------------------------------
- Models (app/models/): Entità di dominio, logica di business
- Schemas (questo file): DTO per validazione input/output API

I DTO non devono mai essere usati direttamente nel dominio o repository.
Servono solo come contratto tra API e client.
"""
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID
from pydantic import BaseModel, Field, model_validator


# --- TYPE DEFINITIONS ---

ColorLiteral = Literal["green", "purple", "orange", "cyan", "pink", "yellow"]
"""
Colori disponibili per le task.

Questi colori sono usati dal frontend per categorizzazione visiva
e filtraggio delle task. Pydantic valida automaticamente che solo
questi valori siano accettati.
"""


# --- BASE SCHEMAS ---

class TaskBase(BaseModel):
    """
    Schema di base per una task, contiene tutti i campi modificabili dall'utente.
    
    Usato come classe base per TaskCreate e per rappresentare
    gli update (PUT requests). Contiene tutte le informazioni
    della task eccetto i campi di sistema (id, tenant_id, created_at).
    
    Attributes:
        title: Titolo breve della task (1-150 caratteri)
        description: Descrizione dettagliata (1-255 caratteri)
        color: Colore per categorizzazione visiva (vedi ColorLiteral)
        date_time: Data/ora di inizio della task
        end_time: Data/ora di fine (opzionale, mutualmente esclusivo con duration_minutes)
        duration_minutes: Durata in minuti (opzionale, 5-1440, mutualmente esclusivo con end_time)
        completed: Flag di completamento (default False)
    
    Validations:
        - title non vuoto, max 150 caratteri
        - description non vuota, max 255 caratteri
        - color deve essere uno dei valori in ColorLiteral
        - duration_minutes tra 5 e 1440 (5 min - 24 ore)
        - end_time e duration_minutes mutuamente esclusivi (validator custom)
        - end_time deve essere dopo date_time (validator custom)
    
    Note:
        - Le validazioni temporali sono critiche per la logica di scheduling
        - Il frontend dovrebbe impedire input invalidi, ma il backend deve validare
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Titolo della task"
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Descrizione dettagliata della task (supporta contenuto rich-text JSON)"
    )
    color: ColorLiteral = Field(
        default="green",
        description="Colore per categorizzazione visiva"
    )
    date_time: datetime = Field(
        ...,
        description="Data/ora di inizio della task"
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="Data/ora di fine (opzionale, mutualmente esclusivo con duration_minutes)"
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        ge=5,
        le=1440,
        description="Durata in minuti (5-1440, opzionale, mutualmente esclusivo con end_time)"
    )
    completed: bool = Field(
        default=False,
        description="Flag di completamento"
    )

    @model_validator(mode="after")
    def check_time_constraints(self):
        """
        Valida i vincoli temporali della task.
        
        Validazioni:
        1. end_time e duration_minutes sono mutuamente esclusivi
           (l'utente può specificare uno o l'altro, non entrambi)
        2. Se end_time è specificato, deve essere successivo a date_time
        
        Raises:
            ValueError: Se le validazioni falliscono
        
        Note:
            - Questo validator viene eseguito DOPO la validazione dei singoli campi
            - Permette validazioni cross-field che Pydantic non può fare automaticamente
        """
        # Validazione 1: mutua esclusività
        if self.end_time and self.duration_minutes:
            raise ValueError(
                "Puoi impostare solo end_time oppure duration_minutes, non entrambi."
            )
        
        # Validazione 2: end_time deve essere dopo date_time
        if self.end_time and self.end_time <= self.date_time:
            raise ValueError(
                "La data di fine deve essere successiva alla data di inizio."
            )
        
        return self


# --- INPUT SCHEMAS ---

class TaskCreate(TaskBase):
    """
    Schema DTO per la creazione di una nuova task.
    
    Identico a TaskBase - l'utente fornisce tutti i campi della task
    ECCETTO il tenant_id, che viene determinato automaticamente dal
    Service Layer in base all'utente autenticato.
    
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
    
    Security:
        - Il tenant_id NON può essere specificato dall'utente
        - Viene ricavato dal JWT token dall'AuthService
        - Questo previene che un utente crei task per altri tenant
    """
    pass  # Nessun campo aggiuntivo, eredita tutto da TaskBase


# --- OUTPUT SCHEMAS ---

class Task(TaskBase):
    """
    Schema DTO completo di una task, include i campi di sistema.
    
    Questo schema rappresenta una task come restituita dalle API
    (GET, POST, PUT). Include tutti i campi di TaskBase più
    i campi di sistema generati dal database.
    
    Attributes:
        (da TaskBase): title, description, color, date_time, end_time, 
                       duration_minutes, completed
        id: UUID univoco della task (generato dal database)
        tenant_id: UUID del tenant proprietario (determinato dal backend)
        created_at: Timestamp di creazione (generato dal database)
    
    Example Response:
        GET /tasks
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
        - Il tenant_id è visibile nel response (utile per debug/verifica)
        - created_at è readonly, mai modificabile dall'utente
        - id è immutabile dopo la creazione
    """
    id: UUID = Field(
        ...,
        description="Identificatore univoco della task"
    )
    tenant_id: UUID = Field(
        ...,
        description="Identificatore del tenant proprietario"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp di creazione (generato automaticamente)"
    )

    class Config:
        """
        Configurazione Pydantic per mapping da oggetti/dict.
        
        from_attributes=True: Permette la conversione automatica da:
        - Oggetti con attributi (es. dataclass, SQLAlchemy models)
        - Dict (come restituiti dal repository)
        """
        from_attributes = True

