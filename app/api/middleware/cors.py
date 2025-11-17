"""
Configurazione CORS (Cross-Origin Resource Sharing) per l'applicazione.

CORS permette al frontend (su Vercel o localhost) di comunicare con il backend,
anche se servito da domini diversi.

Security: Whitelist specifici domini invece di regex generiche per maggiore sicurezza.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def configure_cors(app: FastAPI) -> None:
    """
    Configura il middleware CORS sull'applicazione FastAPI.
    
    Questa funzione aggiunge il middleware CORS con configurazioni
    appropriate per permettere richieste cross-origin dal frontend.
    
    Args:
        app: Istanza dell'applicazione FastAPI
    
    Configurazione:
        - allow_origins: Lista di origini permesse (localhost in sviluppo)
        - allow_origin_regex: Pattern regex per origini dinamiche (Vercel)
        - allow_credentials: Permette invio di cookies e header Authorization
        - allow_methods: Permette tutti i metodi HTTP (GET, POST, PUT, DELETE, etc.)
        - allow_headers: Permette tutti gli header (incluso Authorization)
    
    Note:
        - In produzione considera di limitare allow_methods e allow_headers
        - allow_origin_regex permette qualsiasi sottodominio .vercel.app
        - allow_credentials=True è necessario per JWT Bearer tokens
    
    Security:
        - NON usare allow_origins=["*"] con allow_credentials=True
        - Specifica sempre origini esplicite o usa regex precisi
        - Valuta l'uso di allow_methods specifici in produzione
    """
    # Configurazione CORS con whitelist specifica invece di regex generica
    # In produzione, specificare domini esatti invece di pattern generici
    allowed_origins = [
        "http://localhost:3000",              # Sviluppo locale (Vite default port)
        "http://localhost:5173",              # Sviluppo locale (Vite alternative port)
    ]
    
    # Aggiungi origini da variabile d'ambiente per produzione
    # Formato: CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
    cors_env_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "")
    if cors_env_origins:
        allowed_origins.extend([origin.strip() for origin in cors_env_origins.split(",")])
    
    # In sviluppo, permette anche localhost su altre porte per flessibilità
    # In produzione, rimuovere questo e usare solo CORS_ALLOWED_ORIGINS
    from app.core.config import ENVIRONMENT
    if ENVIRONMENT == "development":
        # Permette localhost su qualsiasi porta per sviluppo
        allow_origin_regex = r"http://localhost:\d+"
    else:
        # In produzione, nessun regex generico
        allow_origin_regex = None
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins if allowed_origins else None,
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,                   # Permette cookies e Authorization header
        # Limitare metodi HTTP solo a quelli necessari (security best practice)
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        # Limitare header solo a quelli necessari (security best practice)
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "X-Requested-With",
            "X-XSRF-TOKEN"  # CSRF token header
        ],
        # Header esposti al client
        expose_headers=[
            "Content-Type",
            "Content-Length",
            "X-XSRF-TOKEN"  # CSRF token per lettura dal client
        ],
        max_age=86400,  # Cache preflight requests per 24 ore
    )

