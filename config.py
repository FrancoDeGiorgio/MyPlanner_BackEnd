"""
Configurazione dell'applicazione e caricamento variabili d'ambiente.
"""
import os

# --- CARICAMENTO VARIABILI D'AMBIENTE (SOLO PER SVILUPPO LOCALE/FALLBACK) ---
# Render inietterà queste variabili nell'ambiente
try:
    # Usiamo dotenv solo se è installato e se stiamo caricando localmente
    from dotenv import load_dotenv
    if not os.environ.get("RENDER"):  # Non caricare da .env se siamo su Render
        load_dotenv()
except ImportError:
    pass

# --- CONFIGURAZIONE E VARIABILI D'AMBIENTE ---
# CRITICO: Render DEVE fornire queste variabili!
# Userà il valore di Render se esiste, altrimenti il fallback.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:fallback_password@fallback_host:5432/postgres"  # Fallback sicuro
)

SECRET_KEY = os.environ.get("SECRET_KEY", "IL_TUO_SEGRETO_JWT_SUPER_SICURO_FALLBACK")  # Fallback sicuro
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


