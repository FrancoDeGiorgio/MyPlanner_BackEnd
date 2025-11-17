"""
DTO Layer - Data Transfer Objects (Pydantic schemas).

Contiene i modelli Pydantic per:
- Validazione input API
- Serializzazione output API
- Documentazione automatica OpenAPI

Separati dai domain models per mantenere API e business logic disaccoppiate.
"""

from .user_settings import (
    UserSettingsBase,
    UserSettingsUpdate,
    UserSettingsResponse,
)

__all__ = [
    "UserSettingsBase",
    "UserSettingsUpdate",
    "UserSettingsResponse",
]

