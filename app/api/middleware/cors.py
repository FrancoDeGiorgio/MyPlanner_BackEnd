"""
Configurazione CORS (Cross-Origin Resource Sharing) per l'applicazione.

CORS permette al frontend (su Vercel o localhost) di comunicare con il backend,
anche se servito da domini diversi.
"""
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",              # Sviluppo locale (Vite default port)
            "http://localhost:5173",              # Sviluppo locale (Vite alternative port)
        ],
        allow_origin_regex=r"https://.*\.vercel\.app",  # Deploy su Vercel (qualsiasi sottodominio)
        allow_credentials=True,                   # Permette cookies e Authorization header
        allow_methods=["*"],                      # Permette GET, POST, PUT, DELETE, OPTIONS, etc.
        allow_headers=["*"],                      # Permette tutti gli header (incluso Authorization, Content-Type)
    )

