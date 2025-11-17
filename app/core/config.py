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
# CRITICO: SECRET_KEY è OBBLIGATORIA in tutti gli ambienti per sicurezza!
# Generare con: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY = os.environ.get("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY è obbligatoria e deve essere impostata come variabile d'ambiente. "
        "Genera una chiave sicura con: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )

# Valida che SECRET_KEY sia abbastanza lunga (minimo 32 caratteri)
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        f"SECRET_KEY deve essere almeno 32 caratteri (attuale: {len(SECRET_KEY)} caratteri). "
        "Genera una chiave sicura con: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )

# Algoritmo di firma JWT (HS256 è lo standard per token simmetrici)
ALGORITHM = "HS256"

# Durata validità del token JWT in minuti
# Dopo questo periodo l'utente dovrà rifare login
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Refresh token expire (7 giorni)
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# JWT Issuer e Audience per validazione rigorosa
JWT_ISSUER = os.environ.get("JWT_ISSUER", "myplanner-api")
JWT_AUDIENCE = os.environ.get("JWT_AUDIENCE", "myplanner-users")


# --- CONFIGURAZIONE APPLICAZIONE ---
# Questi parametri potrebbero essere sovrascritti da variabili d'ambiente
# se necessario per ambienti diversi (dev/staging/prod)

APP_NAME = os.environ.get("APP_NAME", "MyPlanner API")
APP_VERSION = os.environ.get("APP_VERSION", "2.0.0")

# Debug mode (disabilitare in produzione!)
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

# Ambiente di esecuzione (deve essere definito prima di SECRET_KEY per la validazione)
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")  # development, staging, production

# Preferenze utente
DEFAULT_ACCENT_COLOR = os.environ.get("DEFAULT_ACCENT_COLOR", "#7A5BFF")

