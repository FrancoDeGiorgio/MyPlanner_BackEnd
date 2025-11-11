"""initial_schema_from_existing_db

Revision ID: 001
Revises: 
Create Date: 2025-11-06 14:58:00.000000

Questa migrazione rappresenta lo schema esistente del database.
NON deve essere eseguita con `alembic upgrade` se il database esiste già.
Usare invece `alembic stamp head` per marcare il database come aggiornato.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Crea lo schema completo del database MyPlanner.

    Questa migrazione deve essere eseguita normalmente con `alembic upgrade head`
    quando si inizializza un nuovo ambiente.

    Se si collega un database esistente (già allineato manualmente), usare
    `alembic stamp head` per registrare lo stato corrente senza rieseguire le DDL.
    """
    
    # --- STEP 0: Estensioni richieste ---
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
    
    # --- STEP 1: Crea ruolo authenticated ---
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticated') THEN
            CREATE ROLE authenticated NOLOGIN;
        END IF;
    END
    $$;
    """)
    
    # --- STEP 2: Crea tabella users ---
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name_user', sa.String(length=50), nullable=False),
        sa.Column('hashed_password', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='users_pkey'),
        sa.UniqueConstraint('name_user', name='users_name_user_key'),
        comment='Utenti registrati nel sistema (multi-tenant)'
    )
    
    # Indice su name_user per performance
    op.create_index('idx_users_name_user', 'users', ['name_user'], unique=False)
    
    # --- STEP 3: Crea tabella tasks ---
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=20), server_default='green', nullable=False),
        sa.Column('date_time', sa.TIMESTAMP(), nullable=False),
        sa.Column('end_time', sa.TIMESTAMP(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('duration_minutes IS NULL OR duration_minutes >= 5', name='chk_duration'),
        sa.CheckConstraint('end_time IS NULL OR end_time > date_time', name='chk_end_time'),
        sa.ForeignKeyConstraint(['tenant_id'], ['users.id'], name='tasks_tenant_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='tasks_pkey'),
        comment='Attività degli utenti (multi-tenant con RLS)'
    )
    
    # --- STEP 4: Crea indici per performance ---
    op.create_index('idx_tasks_tenant_id', 'tasks', ['tenant_id'], unique=False)
    op.create_index('idx_tasks_date_time', 'tasks', ['date_time'], unique=False)
    op.create_index('idx_tasks_completed', 'tasks', ['completed'], unique=False)
    op.create_index('idx_tasks_tenant_date', 'tasks', ['tenant_id', 'date_time'], unique=False)
    
    # --- STEP 5: Crea funzione trigger per updated_at ---
    op.execute("""
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)
    
    # --- STEP 6: Crea trigger su tasks ---
    op.execute("""
    DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;
    CREATE TRIGGER update_tasks_updated_at
        BEFORE UPDATE ON tasks
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # --- STEP 7: Concedi permessi al ruolo authenticated ---
    op.execute("GRANT ALL PRIVILEGES ON TABLE users TO authenticated;")
    op.execute("GRANT ALL PRIVILEGES ON TABLE tasks TO authenticated;")
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;")


def downgrade() -> None:
    """
    Elimina completamente lo schema del database.
    
    ATTENZIONE: Questo eliminerà TUTTI i dati!
    Usare con cautela, tipicamente solo in ambienti di test.
    """
    # Drop trigger e funzione
    op.execute("DROP TRIGGER IF EXISTS update_tasks_updated_at ON tasks;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;")
    
    # Drop tabelle (CASCADE elimina anche le FK)
    op.drop_table('tasks')
    op.drop_table('users')
    
    # Drop ruolo
    op.execute("DROP ROLE IF EXISTS authenticated;")

