"""
Service layer per la gestione delle impostazioni utente.
"""
from typing import Dict, Any

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.repositories.user_settings_repository import UserSettingsRepository
from app.schemas.user_settings import (
    UserSettingsUpdate,
    UserSettingsResponse,
)


class UserSettingsService:
    """Gestisce la business logic relativa alle impostazioni utente."""

    def __init__(self):
        self.user_repository = UserRepository()
        self.settings_repository = UserSettingsRepository()

    def _get_user_id(self, db: Session, username: str):
        user = self.user_repository.get_user_by_username(db, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return user.id

    def get_settings(self, db: Session, username: str) -> UserSettingsResponse:
        """
        Recupera le impostazioni correnti dell'utente, creando i default se mancanti.
        """
        user_id = self._get_user_id(db, username)
        settings = self.settings_repository.get_by_user_id(db, user_id)

        if settings is None:
            settings = self.settings_repository.create_defaults(db, user_id)

        return UserSettingsResponse.model_validate(settings)

    def update_settings(
        self,
        db: Session,
        username: str,
        payload: UserSettingsUpdate,
    ) -> UserSettingsResponse:
        """
        Aggiorna le impostazioni dell'utente con i valori forniti.
        """
        user_id = self._get_user_id(db, username)
        updates: Dict[str, Any] = payload.model_dump(exclude_unset=True)

        if not updates:
            settings = self.settings_repository.get_by_user_id(db, user_id)
            if settings is None:
                settings = self.settings_repository.create_defaults(db, user_id)
            return UserSettingsResponse.model_validate(settings)

        settings = self.settings_repository.update_settings(db, user_id, updates)
        return UserSettingsResponse.model_validate(settings)


