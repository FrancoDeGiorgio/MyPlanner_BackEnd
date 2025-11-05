"""
Domain Models per Auth.

Definisce le entità del dominio autenticazione come oggetti Python puri.
Questi modelli rappresentano le entità di business indipendentemente
da come vengono persistite nel database o serializzate nelle API.
"""
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class User:
    """
    Entità di dominio che rappresenta un utente/tenant del sistema.
    
    Questo è il modello di dominio "ricco" che rappresenta un utente
    nella logica di business. È indipendente da:
    - Come l'utente viene salvato nel database (Repository Layer)
    - Come l'utente viene serializzato nelle API (Schema/DTO Layer)
    
    Attributes:
        id: Identificatore univoco UUID dell'utente
        name_user: Username univoco, usato anche come tenant identifier per RLS
        hashed_password: Password hashata con bcrypt (mai password in chiaro!)
        created_at: Timestamp di creazione dell'account
    
    Note:
        - Questo modello potrebbe contenere metodi di business logic se necessario
          (es. validazioni di dominio, calcoli, state transitions)
        - Per ora è un semplice data container (dataclass)
        - Separato dai Pydantic schemas per mantenere il dominio indipendente dall'API
    
    Design Pattern:
        - Segue il pattern "Domain Model" dell'architettura a layer
        - Nel nostro progetto è principalmente documentativo, ma in sistemi
          più complessi conterrebbe logica di dominio significativa
    """
    id: UUID
    name_user: str
    hashed_password: str
    created_at: datetime
    
    def __repr__(self) -> str:
        """
        Rappresentazione string-safe dell'utente (senza password).
        
        IMPORTANTE: Non includere mai l'hashed_password nei log o repr!
        """
        return f"User(id={self.id}, name_user='{self.name_user}', created_at={self.created_at})"

