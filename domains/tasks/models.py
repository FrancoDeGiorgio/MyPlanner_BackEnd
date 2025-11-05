"""
Domain Models per Tasks.

Definisce le entità del dominio task come oggetti Python puri.
Questi modelli rappresentano le entità di business indipendentemente
da come vengono persistite o serializzate.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class Task:
    """
    Entità di dominio che rappresenta una task/attività.
    
    Questo è il modello di dominio "ricco" che rappresenta una task
    nella logica di business. È indipendente da:
    - Come la task viene salvata nel database (Repository Layer)
    - Come la task viene serializzata nelle API (Schema/DTO Layer)
    
    Attributes:
        id: Identificatore univoco UUID della task
        tenant_id: UUID del tenant (utente) proprietario della task
        title: Titolo breve della task (max 150 caratteri)
        description: Descrizione dettagliata della task (max 255 caratteri)
        color: Colore associato per categorizzazione visiva
        date_time: Data/ora di inizio della task
        end_time: Data/ora di fine (opzionale, mutualmente esclusivo con duration_minutes)
        duration_minutes: Durata in minuti (opzionale, mutualmente esclusivo con end_time)
        completed: Flag che indica se la task è completata
        created_at: Timestamp di creazione della task
    
    Business Rules:
        - end_time e duration_minutes sono mutuamente esclusivi
        - Se end_time è specificato, deve essere dopo date_time
        - duration_minutes deve essere tra 5 e 1440 (24 ore)
        - Le validazioni sono applicate dal Schema Layer prima di arrivare qui
    
    Note:
        - Questo modello potrebbe contenere metodi di business logic
          (es. calcolare durata effettiva, verificare se in ritardo, ecc.)
        - Per ora è un semplice data container (dataclass)
        - Separato dai Pydantic schemas per mantenere il dominio indipendente dall'API
    
    Design Pattern:
        - Segue il pattern "Domain Model" dell'architettura a layer
        - In sistemi complessi conterrebbe logica di dominio significativa
    """
    id: UUID
    tenant_id: UUID
    title: str
    description: str
    color: str  # "green", "purple", "orange", "cyan", "pink", "yellow"
    date_time: datetime
    end_time: Optional[datetime]
    duration_minutes: Optional[int]
    completed: bool
    created_at: datetime
    
    def get_effective_duration(self) -> Optional[int]:
        """
        Calcola la durata effettiva della task in minuti.
        
        Returns:
            int: Durata in minuti se disponibile, None altrimenti
        
        Note:
            - Se duration_minutes è specificato, lo restituisce
            - Se end_time è specificato, calcola la differenza in minuti
            - Se nessuno dei due, restituisce None
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
        
        Args:
            current_time: Timestamp corrente per il confronto
        
        Returns:
            bool: True se la task è scaduta e non completata, False altrimenti
        
        Note:
            - Una task completata non è mai considerata in ritardo
            - Confronta con end_time se disponibile, altrimenti con date_time
        """
        if self.completed:
            return False
        
        deadline = self.end_time if self.end_time else self.date_time
        return deadline < current_time if deadline else False
    
    def __repr__(self) -> str:
        """Rappresentazione string della task per debug/logging."""
        status = "✓" if self.completed else "○"
        return f"Task({status} {self.title} @ {self.date_time}, tenant={self.tenant_id})"

