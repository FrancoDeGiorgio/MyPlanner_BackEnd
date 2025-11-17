# ============================================================================
# DOCKERFILE BACKEND - MyPlanner API (FastAPI)
# ============================================================================
# Questo Dockerfile crea un'immagine Docker per l'applicazione backend FastAPI.
# Utilizza Python 3.11-slim come base per un'immagine più leggera rispetto
# alla versione standard di Python.

FROM python:3.11-slim AS base

# ============================================================================
# VARIABILI D'AMBIENTE PYTHON
# ============================================================================
# PYTHONDONTWRITEBYTECODE=1: Evita la creazione di file .pyc (bytecode Python)
#                            che non sono necessari nel container e occupano spazio
# PYTHONUNBUFFERED=1: Disabilita il buffering dell'output Python, permettendo
#                     di vedere i log in tempo reale (utile per debugging)
# PIP_NO_CACHE_DIR=off: Mantiene la cache di pip (può essere utile per rebuild)
# PIP_DISABLE_PIP_VERSION_CHECK=on: Evita controlli di versione pip che rallentano
#                                   l'installazione e possono causare warning
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# ============================================================================
# DIRECTORY DI LAVORO
# ============================================================================
# Imposta la directory di lavoro all'interno del container dove verranno
# copiati i file dell'applicazione e dove verrà eseguito il codice
WORKDIR /app

# ============================================================================
# INSTALLAZIONE DIPENDENZE DI SISTEMA
# ============================================================================
# build-essential: Include compilatori C/C++ (gcc, make, ecc.) necessari per
#                  compilare alcune dipendenze Python native come psycopg2-binary
# libpq-dev: Librerie di sviluppo PostgreSQL necessarie per compilare psycopg2
#            (driver Python per PostgreSQL)
# netcat-openbsd: Strumento di rete utilizzato dallo script entrypoint.sh per
#                 verificare se il database PostgreSQL è pronto prima di avviare l'app
# curl: Necessario per HEALTHCHECK
# --no-install-recommends: Installa solo i pacchetti essenziali, senza raccomandazioni
#                          per ridurre la dimensione dell'immagine
# rm -rf /var/lib/apt/lists/*: Rimuove le liste dei pacchetti apt dopo l'installazione
#                               per ridurre ulteriormente la dimensione dell'immagine
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libpq-dev netcat-openbsd curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# INSTALLAZIONE DIPENDENZE PYTHON
# ============================================================================
# Copia prima solo il file requirements.txt (separazione dei layer Docker)
# Questo permette a Docker di utilizzare la cache se requirements.txt non cambia,
# evitando di reinstallare tutte le dipendenze ad ogni build
COPY requirements.txt ./

# Aggiorna pip all'ultima versione e installa tutte le dipendenze Python
# --no-cache-dir: Non salva la cache di pip per ridurre la dimensione dell'immagine
#                 (nota: questo può rallentare rebuild successivi)
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ============================================================================
# CREAZIONE UTENTE NON-ROOT
# ============================================================================
# Crea un utente non-root per eseguire l'applicazione (security best practice)
# UID 1001 è comune per applicazioni utente
# --no-create-home: Non crea directory home (non necessaria)
# --disabled-password: Disabilita login password (solo per esecuzione container)
RUN groupadd -r appgroup --gid=1001 \
    && useradd -r -g appgroup --uid=1001 --home-dir=/app --shell=/bin/bash appuser

# ============================================================================
# COPIA CODICE DELL'APPLICAZIONE
# ============================================================================
# Copia tutto il codice dell'applicazione nella directory di lavoro /app
# Questo viene fatto dopo l'installazione delle dipendenze per sfruttare meglio
# la cache di Docker: se solo il codice cambia, le dipendenze non vengono reinstallate
COPY . .

# ============================================================================
# CONFIGURAZIONE ENTRYPOINT
# ============================================================================
# Copia lo script entrypoint.sh nella root del container e lo rende eseguibile
# Lo script entrypoint.sh gestisce:
#   1. Attesa che il database PostgreSQL sia pronto (usando netcat)
#   2. Esecuzione delle migrazioni database con Alembic
#   3. Avvio dell'applicazione FastAPI con uvicorn
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ============================================================================
# IMPOSTA OWNERSHIP E PERMESSI
# ============================================================================
# Cambia ownership di /app all'utente non-root
# Questo permette all'applicazione di leggere/scrivere nella directory di lavoro
RUN chown -R appuser:appgroup /app

# ============================================================================
# ESPOSIZIONE PORTA
# ============================================================================
# Espone la porta 8000 su cui l'applicazione FastAPI sarà in ascolto
# Questa è solo una documentazione: l'esposizione effettiva avviene nel docker-compose.yml
EXPOSE 8000

# ============================================================================
# HEALTHCHECK
# ============================================================================
# Verifica periodicamente che l'applicazione sia in esecuzione e risponda correttamente
# --interval=30s: Controlla ogni 30 secondi
# --timeout=3s: Timeout di 3 secondi per la richiesta
# --start-period=40s: Aspetta 40 secondi prima del primo controllo (tempo di avvio)
# --retries=3: Dopo 3 tentativi falliti consecutivi, il container è considerato unhealthy
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ============================================================================
# SWITCH A UTENTE NON-ROOT
# ============================================================================
# Cambia da root a utente non-root prima di eseguire l'applicazione
# Questo riduce il rischio di privilege escalation se l'applicazione viene compromessa
USER appuser

# ============================================================================
# COMANDO DI AVVIO
# ============================================================================
# ENTRYPOINT definisce il comando che viene sempre eseguito quando il container parte
# Lo script entrypoint.sh gestisce l'intero processo di inizializzazione e avvio
# Usa la forma array per evitare problemi con il parsing della shell
ENTRYPOINT ["/entrypoint.sh"]


