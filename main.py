"""
Applicazione FastAPI principale - Planner Attività Multi-Tenant con RLS.
Struttura modulare con router separati per autenticazione e gestione tasks.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, tasks

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
        "https://*.vercel.app",               # Tutte le app Vercel
        #"*"                                   # Temporaneo: accetta da qualsiasi origine
    ],
    allow_credentials=True,
    allow_methods=["*"],      # Permette GET, POST, PUT, DELETE, ecc.
    allow_headers=["*"],      # Permette tutti gli header (incluso Authorization)
)

# --- REGISTRAZIONE ROUTER ---

app.include_router(auth.router)
app.include_router(tasks.router)


# --- ENDPOINT ROOT (OPZIONALE) ---

@app.get("/", tags=["Root"])
def read_root():
    """Endpoint di benvenuto."""
    return {
        "message": "Planner API Multi-Tenant with RLS",
        "version": "2.0.0",
        "docs": "/docs"
    }
