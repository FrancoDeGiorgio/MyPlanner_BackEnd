"""
DEPRECATO: Questo file è stato sostituito dall'architettura a domini.

Gli schemi Pydantic sono stati spostati nei rispettivi domini:
- Auth schemas: domains/auth/schemas.py
  * Token, TokenData, UserBase, UserCreate
  
- Tasks schemas: domains/tasks/schemas.py
  * TaskBase, TaskCreate, Task, ColorLiteral

PER COMPATIBILITÀ TEMPORANEA:
Se hai codice legacy che importa da questo file, aggiorna gli import:

Vecchio import:
    from schemas import Token, UserCreate

Nuovo import:
    from domains.auth.schemas import Token, UserCreate

Vecchio import:
    from schemas import Task, TaskCreate

Nuovo import:
    from domains.tasks.schemas import Task, TaskCreate

QUESTO FILE SARÀ RIMOSSO IN UNA VERSIONE FUTURA.
"""

# Import temporanei per backward compatibility (da rimuovere dopo migrazione completa)
from domains.auth.schemas import Token, TokenData, UserBase, UserCreate
from domains.tasks.schemas import TaskBase, TaskCreate, Task, ColorLiteral

__all__ = [
    "Token",
    "TokenData",
    "UserBase",
    "UserCreate",
    "TaskBase",
    "TaskCreate",
    "Task",
    "ColorLiteral"
]
