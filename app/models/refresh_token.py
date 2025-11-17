"""
Modello RefreshToken per gestione refresh token con blacklist.

Questo modello permette di:
- Tracciare i refresh token emessi
- Implementare token rotation (ogni refresh genera nuovo token)
- Revocare token compromessi (blacklist)
- Pulire automaticamente token scaduti
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class RefreshToken(Base):
    """
    Modello per refresh token con supporto blacklist e rotation.
    
    Attributes:
        id: UUID univoco del record
        token_hash: Hash SHA256 del refresh token (non salviamo il token in chiaro)
        user_id: ID dell'utente proprietario del token
        expires_at: Timestamp di scadenza del token
        revoked: Flag per indicare se il token è stato revocato (blacklist)
        created_at: Timestamp di creazione
        replaced_by_token_hash: Hash del token che ha sostituito questo (per rotation)
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA256 hash
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    replaced_by_token_hash = Column(String(64), nullable=True)  # Per token rotation
    
    # Relationship
    user = relationship("User", back_populates="refresh_tokens")
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, revoked={self.revoked})>"

