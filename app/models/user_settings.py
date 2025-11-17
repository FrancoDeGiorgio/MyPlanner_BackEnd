"""
Domain Model per UserSettings - Impostazioni profilo utente.

Gestisce le preferenze linguistiche dell'utente.
"""
from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class UserSettings(Base):
    """
    Impostazioni del profilo utente.
    
    Questa tabella memorizza le preferenze personalizzate di ogni utente.
    Relazione 1:1 con User.
    
    Attributes:
        id: Identificatore univoco delle impostazioni
        user_id: Foreign key verso la tabella users (relazione 1:1)
        language: Lingua preferita dell'utente (it, en, etc.)
        theme: Tema interfaccia utente (light, dark)
        created_at: Timestamp di creazione
        updated_at: Timestamp ultimo aggiornamento
    """
    __tablename__ = 'user_settings'
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        nullable=False,
        comment="Identificatore univoco impostazioni"
    )
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,  # Relazione 1:1 con User
        nullable=False,
        index=True,
        comment="Riferimento all'utente"
    )
    
    language = Column(
        String(5),
        server_default='it',
        nullable=False,
        comment="Codice lingua ISO (it, en, es, fr, etc.)"
    )
    
    theme = Column(
        String(20),
        server_default='light',
        nullable=False,
        comment="Tema interfaccia utente (light, dark)"
    )

    accent_color = Column(
        String(20),
        server_default='#7A5BFF',
        nullable=False,
        comment="Colore accento interfaccia (HEX)"
    )
    
    created_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Data creazione"
    )
    
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        nullable=False,
        comment="Data ultimo aggiornamento"
    )
    
    # --- RELATIONSHIPS ---
    user = relationship(
        "User",
        back_populates="settings",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        """Rappresentazione leggibile delle impostazioni."""
        return (
            "UserSettings("
            f"user_id={self.user_id}, language='{self.language}', "
            f"theme='{self.theme}', accent_color='{self.accent_color}'"
            ")"
        )

