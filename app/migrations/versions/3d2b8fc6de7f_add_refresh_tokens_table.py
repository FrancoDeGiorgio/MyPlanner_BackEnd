"""add_refresh_tokens_table

Revision ID: 3d2b8fc6de7f
Revises: 2c1a7ec5ca1b
Create Date: 2025-01-15 10:00:00.000000

Aggiunge tabella refresh_tokens per gestione refresh token con blacklist e rotation.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "3d2b8fc6de7f"
down_revision: Union[str, None] = "2c1a7ec5ca1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Crea la tabella refresh_tokens per gestione refresh token con blacklist.
    
    La tabella permette di:
    - Tracciare i refresh token emessi (hash SHA256)
    - Implementare token rotation (ogni refresh genera nuovo token)
    - Revocare token compromessi (blacklist tramite flag revoked)
    - Pulire automaticamente token scaduti
    """
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Identificatore univoco del record"
        ),
        sa.Column(
            "token_hash",
            sa.String(length=64),
            nullable=False,
            unique=True,
            index=True,
            comment="Hash SHA256 del refresh token (non salviamo il token in chiaro)"
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
            comment="ID dell'utente proprietario del token"
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
            comment="Timestamp di scadenza del token"
        ),
        sa.Column(
            "revoked",
            sa.Boolean(),
            default=False,
            nullable=False,
            index=True,
            comment="Flag per indicare se il token è stato revocato (blacklist)"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
            comment="Timestamp di creazione"
        ),
        sa.Column(
            "replaced_by_token_hash",
            sa.String(length=64),
            nullable=True,
            comment="Hash del token che ha sostituito questo (per rotation)"
        ),
        comment="Tabella per gestione refresh token con blacklist e rotation"
    )
    
    # Indice composto per query frequenti
    op.create_index(
        "ix_refresh_tokens_user_id_revoked",
        "refresh_tokens",
        ["user_id", "revoked"]
    )


def downgrade() -> None:
    """Rimuove la tabella refresh_tokens."""
    op.drop_index("ix_refresh_tokens_user_id_revoked", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

