"""
Applicazione FastAPI principale - Planner Attività Multi-Tenant con RLS.

Architettura a Layer Organizzata:
- app/api/: Presentation layer (routes, middleware, dependencies)
- app/services/: Business logic layer
- app/repositories/: Data access layer
- app/models/: Domain models (entità business)
- app/schemas/: DTO layer (Pydantic per validazione API)
- app/core/: Configurazione e infrastruttura centrale
- app/utils/: Utilities condivise

Questa struttura segue i principi dell'architettura a layer moderna,
separando le responsabilità e permettendo:
- Testabilità: ogni layer può essere testato indipendentemente
- Manutenibilità: modifiche isolate senza side-effects
- Scalabilità: facile aggiungere nuovi domini
- Riusabilità: service e repository condivisibili
"""
from fastapi import FastAPI

# Import aggiornati per la nuova architettura
from app.api.routes import auth, tasks, postman, settings
from app.api.middleware.cors import configure_cors
from app.api.middleware.error_handler import configure_error_handlers
from app.api.middleware.rate_limit import configure_rate_limiting
from app.api.middleware.security_headers import configure_security_headers
from app.api.middleware.audit import configure_audit_logging
from app.api.middleware.csrf import configure_csrf_protection
from app.utils.logger import configure_root_logger
from app.core.config import APP_NAME, APP_VERSION


# --- INIZIALIZZAZIONE APP FASTAPI ---

app = FastAPI(
    title=APP_NAME,
    description="Backend per la gestione delle attività protette da RLS.",
    version=APP_VERSION
)


# --- CONFIGURAZIONE LOGGING ---
# Configura il logging strutturato per tutta l'applicazione
configure_root_logger()


# --- CONFIGURAZIONE MIDDLEWARE ---
# IMPORTANTE: L'ordine dei middleware conta!
# Vengono eseguiti dall'ultimo al primo nella catena di richiesta

# 1. Error handlers (devono catturare errori da tutti gli altri middleware)
configure_error_handlers(app)

# 2. Security headers (protezione XSS, clickjacking, HSTS)
configure_security_headers(app)

# 3. Rate limiting (protezione brute force e DoS)
configure_rate_limiting(app)

# 4. Audit logging (tracciamento operazioni critiche)
configure_audit_logging(app)

# 5. CSRF protection (deve essere prima di CORS per gestire cookie)
configure_csrf_protection(app)

# 6. CORS (deve essere dopo error handlers per gestire preflight OPTIONS)
configure_cors(app)


# --- REGISTRAZIONE ROUTER DEI DOMINI ---
# Ogni dominio espone un router con i propri endpoint.
# I router sono configurati con prefix e tags per organizzazione logica.

app.include_router(auth.router)   # /auth/register, /auth/login
app.include_router(tasks.router)  # /tasks (GET, POST, PUT, DELETE)
app.include_router(postman.router)  # /postman (pagina, collection, environment)
app.include_router(settings.router)  # /settings (GET, PUT)


# --- ENDPOINT ROOT (OPZIONALE) ---

@app.get("/", tags=["Root"])
def read_root():
    """
    Endpoint di benvenuto e health check.
    
    Restituisce informazioni base sull'API e link alla documentazione.
    Utile per verificare che il server sia attivo e raggiungibile.
    
    Returns:
        Dict: Informazioni base sull'API
    """
    return {
        "message": "Planner API Multi-Tenant with RLS",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "ok"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Endpoint di health check per monitoring e deployment.
    
    Verifica che l'applicazione sia avviata correttamente.
    Può essere esteso per controllare connessioni database, cache, etc.
    
    Returns:
        Dict: Stato dell'applicazione
    """
    return {
        "status": "healthy",
        "version": APP_VERSION
    }
