"""
Applicazione FastAPI principale - Planner Attività Multi-Tenant con RLS.

Architettura a Layer Organizzata per Dominio:
- Ogni dominio (auth, tasks) ha la propria struttura completa:
  * Router (API Layer): gestione HTTP, validazione input/output
  * Service (Business Logic Layer): orchestrazione e regole di business
  * Repository (Data Access Layer): accesso al database con RLS
  * Models (Domain Layer): entità di dominio
  * Schemas (DTO Layer): validazione e serializzazione API

Questa struttura segue i principi dell'architettura a layer moderna,
separando le responsabilità e permettendo:
- Testabilità: ogni layer può essere testato indipendentemente
- Manutenibilità: modifiche isolate senza side-effects
- Scalabilità: facile aggiungere nuovi domini
- Riusabilità: service e repository condivisibili
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import dei router dai domini
from domains.auth import router as auth_router
from domains.tasks import router as tasks_router

# --- INIZIALIZZAZIONE APP FASTAPI ---

app = FastAPI(
    title="Planner Attività Multi-Tenant (FastAPI + Supabase RLS)",
    description="Backend per la gestione delle attività protette da RLS.",
    version="2.0.0"
)

# --- CONFIGURAZIONE CORS ---
# ⚠️ IMPORTANTE: Permette al frontend su Vercel di comunicare con questo backend

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",              # Sviluppo locale
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",  # Deploy su Vercel (qualsiasi sottodominio)
    allow_credentials=True,
    allow_methods=["*"],      # Permette GET, POST, PUT, DELETE, ecc.
    allow_headers=["*"],      # Permette tutti gli header (incluso Authorization)
)

# --- REGISTRAZIONE ROUTER DEI DOMINI ---
# Ogni dominio espone un router con i propri endpoint.
# I router sono configurati con prefix e tags per organizzazione logica.

app.include_router(auth_router.router)   # /auth/register, /auth/login
app.include_router(tasks_router.router)  # /tasks (GET, POST, PUT, DELETE)


# --- ENDPOINT ROOT (OPZIONALE) ---

@app.get("/", tags=["Root"])
def read_root():
    """Endpoint di benvenuto."""
    return {
        "message": "Planner API Multi-Tenant with RLS",
        "version": "2.0.0",
        "docs": "/docs"
    }
