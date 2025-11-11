"""
Domain Models - Entità di business dell'applicazione con SQLAlchemy ORM.

Contiene le entità di dominio come modelli SQLAlchemy ORM che rappresentano
i concetti core del business e il loro mapping sul database.
"""
from app.core.database import Base
from app.models.user import User
from app.models.task import Task
from app.models.user_settings import UserSettings

__all__ = ["Base", "User", "Task", "UserSettings"]
