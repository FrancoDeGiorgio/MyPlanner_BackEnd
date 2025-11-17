"""
Pydantic Schemas per le impostazioni utente (UserSettings).

Definiscono la struttura e la validazione per le preferenze salvate
dagli utenti, incluse lingua, tema e colore accento personalizzato.
"""
from typing import Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, constr, field_validator

from app.core.config import DEFAULT_ACCENT_COLOR


# --- Type definitions ---

AccentColorHex = constr(pattern=r"^#[0-9A-Fa-f]{6}$")
ThemeLiteral = Literal["light", "dark"]


class UserSettingsBase(BaseModel):
    """
    Schema base per le impostazioni utente.

    Contiene tutti i campi modificabili dal client. Utilizzato come
    base sia per update (PUT) che per output (response).
    """

    language: constr(min_length=2, max_length=5) = Field(
        default="it",
        description="Codice lingua ISO 639-1 (es. it, en, es).",
    )
    theme: ThemeLiteral = Field(
        default="light",
        description="Tema dell'interfaccia utente.",
    )
    accent_color: AccentColorHex = Field(
        default=DEFAULT_ACCENT_COLOR,
        description="Colore accento dell'interfaccia in formato HEX (#RRGGBB).",
    )

    @field_validator("accent_color")
    @classmethod
    def normalize_color(cls, value: str) -> str:
        """
        Normalizza il colore accent, restituendo sempre lettere maiuscole.
        """
        return value.upper()


class UserSettingsUpdate(BaseModel):
    """
    Schema per aggiornamento parziale/complete delle impostazioni.
    Tutti i campi sono opzionali.
    """

    language: Optional[constr(min_length=2, max_length=5)] = Field(
        default=None,
        description="Codice lingua ISO 639-1 (es. it, en, es).",
    )
    theme: Optional[ThemeLiteral] = Field(
        default=None,
        description="Tema dell'interfaccia utente.",
    )
    accent_color: Optional[AccentColorHex] = Field(
        default=None,
        description="Colore accento dell'interfaccia in formato HEX (#RRGGBB).",
    )

    @field_validator("accent_color")
    @classmethod
    def normalize_color(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        return value.upper()


class UserSettingsResponse(UserSettingsBase):
    """
    Schema completo restituito dalle API, include metadati.
    """

    id: UUID = Field(description="Identificatore univoco delle impostazioni.")
    user_id: UUID = Field(description="Identificatore dell'utente associato.")

    class Config:
        from_attributes = True


