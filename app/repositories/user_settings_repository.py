"""
Repository per l'accesso alla tabella user_settings.

Gestisce il recupero e l'aggiornamento delle preferenze utente.
"""
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.models.user_settings import UserSettings


class UserSettingsRepository:
    """Repository per la gestione delle impostazioni utente."""

    def get_by_user_id(self, db: Session, user_id: UUID) -> Optional[UserSettings]:
        """
        Recupera le impostazioni associate a un utente.
        """
        return (
            db.query(UserSettings)
            .filter(UserSettings.user_id == user_id)
            .one_or_none()
        )

    def create_defaults(self, db: Session, user_id: UUID) -> UserSettings:
        """
        Crea un record di impostazioni con valori di default.
        """
        try:
            settings = UserSettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
            return settings
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize user settings.",
            ) from exc

    def update_settings(
        self,
        db: Session,
        user_id: UUID,
        updates: Dict[str, Any],
    ) -> UserSettings:
        """
        Aggiorna i campi forniti per le impostazioni dell'utente.
        """
        try:
            settings = self.get_by_user_id(db, user_id)
            if settings is None:
                settings = UserSettings(user_id=user_id)
                db.add(settings)
                db.flush()

            for field, value in updates.items():
                setattr(settings, field, value)

            db.commit()
            db.refresh(settings)
            return settings
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user settings.",
            ) from exc


