"""
Alembic Migration Environment Configuration.

Questo modulo configura l'ambiente per le migrazioni Alembic, includendo:
- Connessione al database tramite SQLAlchemy
- Caricamento dei metadati dei modelli ORM per autogeneration
- Gestione di migrazioni online e offline
- Supporto per variabili d'ambiente (DATABASE_URL)
"""
from logging.config import fileConfig
import os
import sys
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Aggiungi il parent directory al path per importare i modelli
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '../..')))

# Importa Base e tutti i modelli per autogeneration
from app.core.database import Base
from app.models import User, Task  # Import esplicito per assicurarsi che i modelli siano registrati

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Aggiungi i metadati dei modelli ORM per l'autogeneration
# CRITICO: Questo permette ad Alembic di rilevare automaticamente i cambiamenti
target_metadata = Base.metadata

# Leggi DATABASE_URL da variabili d'ambiente
# Questo è necessario perché non hardcodiamo credenziali in alembic.ini
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)
else:
    # Fallback per sviluppo locale se DATABASE_URL non è impostata
    print("WARNING: DATABASE_URL not set, using default from config")

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Includi oggetti PostgreSQL specifici (ENUM, ecc.)
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Configurazione dell'engine per le migrazioni
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = config.get_main_option("sqlalchemy.url")
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Opzioni per comparazione avanzata
            compare_type=True,  # Rileva cambiamenti nei tipi di colonna
            compare_server_default=True,  # Rileva cambiamenti nei default
            # Includi indici e constraints nella comparazione
            include_object=lambda obj, name, type_, reflected, compare_to: True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

