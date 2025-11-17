"""
Repository per RefreshToken - Data Access Layer.

Gestisce tutte le operazioni di accesso ai dati per i refresh token:
- Creazione e salvataggio token
- Verifica validità token
- Revoca token (blacklist)
- Token rotation
- Pulizia token scaduti
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.refresh_token import RefreshToken
from app.core.config import REFRESH_TOKEN_EXPIRE_DAYS


class RefreshTokenRepository:
    """
    Repository per gestione refresh token con blacklist e rotation.
    
    Responsabilità:
    - Salvare hash dei refresh token nel database
    - Verificare validità e revoca dei token
    - Implementare token rotation (ogni refresh genera nuovo token)
    - Pulire token scaduti
    """
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Genera hash SHA256 del token per storage sicuro.
        
        Args:
            token: Refresh token JWT in chiaro
        
        Returns:
            str: Hash SHA256 del token (64 caratteri hex)
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    def create_token(
        self,
        db: Session,
        token: str,
        user_id: str,
        expires_at: Optional[datetime] = None
    ) -> RefreshToken:
        """
        Crea e salva un nuovo refresh token nel database.
        
        Args:
            db: Sessione SQLAlchemy
            token: Refresh token JWT in chiaro (sarà hashato)
            user_id: UUID dell'utente proprietario
            expires_at: Timestamp di scadenza (default: REFRESH_TOKEN_EXPIRE_DAYS da config)
        
        Returns:
            RefreshToken: Record del token salvato
        """
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        token_hash = self.hash_token(token)
        
        refresh_token = RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            revoked=False
        )
        
        db.add(refresh_token)
        db.commit()
        db.refresh(refresh_token)
        
        return refresh_token
    
    def find_token(self, db: Session, token: str) -> Optional[RefreshToken]:
        """
        Trova un refresh token nel database tramite hash.
        
        Args:
            db: Sessione SQLAlchemy
            token: Refresh token JWT in chiaro
        
        Returns:
            Optional[RefreshToken]: Token trovato o None
        """
        token_hash = self.hash_token(token)
        return db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
    
    def is_token_valid(self, db: Session, token: str) -> bool:
        """
        Verifica se un refresh token è valido (esiste, non revocato, non scaduto).
        
        Args:
            db: Sessione SQLAlchemy
            token: Refresh token JWT in chiaro
        
        Returns:
            bool: True se il token è valido, False altrimenti
        """
        refresh_token = self.find_token(db, token)
        
        if refresh_token is None:
            return False
        
        if refresh_token.revoked:
            return False
        
        if refresh_token.expires_at < datetime.utcnow():
            return False
        
        return True
    
    def revoke_token(self, db: Session, token: str) -> bool:
        """
        Revoca un refresh token (blacklist).
        
        Args:
            db: Sessione SQLAlchemy
            token: Refresh token JWT da revocare
        
        Returns:
            bool: True se revocato con successo, False se non trovato
        """
        refresh_token = self.find_token(db, token)
        
        if refresh_token is None:
            return False
        
        refresh_token.revoked = True
        db.commit()
        
        return True
    
    def revoke_all_user_tokens(self, db: Session, user_id: str) -> int:
        """
        Revoca tutti i refresh token di un utente (utile per logout forzato o cambio password).
        
        Args:
            db: Sessione SQLAlchemy
            user_id: UUID dell'utente
        
        Returns:
            int: Numero di token revocati
        """
        count = db.query(RefreshToken).filter(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False
            )
        ).update({"revoked": True})
        
        db.commit()
        return count
    
    def rotate_token(
        self,
        db: Session,
        old_token: str,
        new_token: str,
        user_id: str
    ) -> RefreshToken:
        """
        Implementa token rotation: revoca il vecchio token e crea uno nuovo.
        
        Args:
            db: Sessione SQLAlchemy
            old_token: Vecchio refresh token da revocare
            new_token: Nuovo refresh token da creare
            user_id: UUID dell'utente
        
        Returns:
            RefreshToken: Nuovo token creato
        """
        # Revoca il vecchio token
        old_refresh_token = self.find_token(db, old_token)
        if old_refresh_token:
            old_refresh_token.revoked = True
            old_refresh_token.replaced_by_token_hash = self.hash_token(new_token)
        
        # Crea il nuovo token
        new_refresh_token = self.create_token(db, new_token, user_id)
        
        db.commit()
        
        return new_refresh_token
    
    def cleanup_expired_tokens(self, db: Session) -> int:
        """
        Elimina tutti i token scaduti dal database (pulizia periodica).
        
        Args:
            db: Sessione SQLAlchemy
        
        Returns:
            int: Numero di token eliminati
        """
        count = db.query(RefreshToken).filter(
            RefreshToken.expires_at < datetime.utcnow()
        ).delete()
        
        db.commit()
        return count

