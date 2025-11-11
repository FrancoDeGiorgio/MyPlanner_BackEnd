"""
Configurazione dell'applicazione e caricamento variabili d'ambiente.

Questo modulo centralizza tutta la configurazione dell'applicazione,
caricando le variabili d'ambiente e fornendo valori di fallback sicuri
per lo sviluppo locale.

Note:
    - In produzione (Render), le variabili vengono iniettate dall'ambiente
    - In sviluppo locale, vengono caricate da .env tramite python-dotenv
    - Non committare mai file .env con credenziali reali!
"""
import os

# --- CARICAMENTO VARIABILI D'AMBIENTE (SOLO PER SVILUPPO LOCALE/FALLBACK) ---
# Render inietterà queste variabili nell'ambiente, quindi .env è solo per sviluppo locale
try:
    # Usiamo dotenv solo se è installato e se stiamo caricando localmente
    from dotenv import load_dotenv
    if not os.environ.get("RENDER"):  # Non caricare da .env se siamo su Render
        load_dotenv()
except ImportError:
    # Se python-dotenv non è installato, va bene comunque
    # (es. in container Docker con env vars già settate)
    pass

# --- CONFIGURAZIONE DATABASE ---
# Le migrazioni Alembic richiedono una stringa di connessione valida.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL non è impostata. "
        "Configura la variabile d'ambiente o il file .env prima di avviare l'applicazione."
    )

# --- CONFIGURAZIONE JWT ---
# CRITICO: In produzione usare una chiave segreta robusta e unica!
# Generare con: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "IL_TUO_SEGRETO_JWT_SUPER_SICURO_FALLBACK"  # Fallback solo per sviluppo
)

# Algoritmo di firma JWT (HS256 è lo standard per token simmetrici)
ALGORITHM = "HS256"

# Durata validità del token JWT in minuti
# Dopo questo periodo l'utente dovrà rifare login
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# --- CONFIGURAZIONE APPLICAZIONE ---
# Questi parametri potrebbero essere sovrascritti da variabili d'ambiente
# se necessario per ambienti diversi (dev/staging/prod)

APP_NAME = os.environ.get("APP_NAME", "MyPlanner API")
APP_VERSION = os.environ.get("APP_VERSION", "2.0.0")

# Debug mode (disabilitare in produzione!)
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# Ambiente di esecuzione
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")  # development, staging, production

# Preferenze utente
DEFAULT_ACCENT_COLOR = os.environ.get("DEFAULT_ACCENT_COLOR", "#7A5BFF")

