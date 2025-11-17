"""
API Router per la gestione delle impostazioni utente.
"""
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.api.middleware.rate_limit import get_global_rate_limit
from app.schemas.user_settings import (
    UserSettingsResponse,
    UserSettingsUpdate,
)
from app.services.user_settings_service import UserSettingsService


router = APIRouter(
    prefix="/settings",
    tags=["User Settings"],
)

settings_service = UserSettingsService()


@router.get(
    "",
    response_model=UserSettingsResponse,
    summary="Recupera le impostazioni dell'utente autenticato",
    dependencies=[Depends(get_global_rate_limit())]  # Rate limit globale: 100 req/min
)
def get_user_settings(
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Restituisce le impostazioni correnti dell'utente. Se non esistono,
    vengono create automaticamente con i valori di default.
    """
    return settings_service.get_settings(db, username)


@router.put(
    "",
    response_model=UserSettingsResponse,
    summary="Aggiorna le impostazioni dell'utente autenticato",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_global_rate_limit())]  # Rate limit globale: 100 req/min
)
def update_user_settings(
    payload: UserSettingsUpdate,
    username: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Aggiorna le impostazioni utente con i valori forniti.
    """
    return settings_service.update_settings(db, username, payload)


