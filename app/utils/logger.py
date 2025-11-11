"""
Configurazione logging strutturato per l'applicazione.

Fornisce logger configurati per diversi ambienti (development, production)
con formattazione appropriata e livelli di log personalizzabili.

Usage:
    >>> from app.utils.logger import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Operazione completata", extra={"user_id": "123"})
"""
import logging
import sys
from typing import Optional
from app.core.config import ENVIRONMENT, DEBUG


# --- CONFIGURAZIONE FORMATO LOG ---

# Formato per development: più leggibile
DEV_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Formato per production: include più metadati per parsing automatico
PROD_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Crea e configura un logger per il modulo specificato.
    
    Il logger viene configurato in base all'ambiente di esecuzione:
    - Development: log più verbosi, formato semplice
    - Production: log essenziali, formato completo con metadati
    
    Args:
        name: Nome del logger (tipicamente __name__ del modulo)
        level: Livello di log opzionale (se None, usa quello di default per l'ambiente)
    
    Returns:
        logging.Logger: Logger configurato
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug info")
        >>> logger.info("Operazione completata")
        >>> logger.warning("Attenzione!")
        >>> logger.error("Errore!")
        >>> logger.critical("Errore critico!")
    
    Livelli di log (dal più al meno verboso):
        - DEBUG: Informazioni dettagliate per debugging
        - INFO: Conferme che le cose funzionano come previsto
        - WARNING: Indicazione che qualcosa di inaspettato è successo
        - ERROR: Errore più serio, il software non è riuscito a fare qualcosa
        - CRITICAL: Errore molto grave, il programma potrebbe non continuare
    """
    # Crea il logger con il nome del modulo
    logger = logging.getLogger(name)
    
    # Evita di aggiungere handler multipli se il logger esiste già
    if logger.handlers:
        return logger
    
    # Determina il livello di log in base all'ambiente
    if level is None:
        if DEBUG or ENVIRONMENT == "development":
            level = logging.DEBUG
        else:
            level = logging.INFO
    
    logger.setLevel(level)
    
    # Crea handler per output su console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Sceglie il formato in base all'ambiente
    if ENVIRONMENT == "production":
        formatter = logging.Formatter(PROD_FORMAT)
    else:
        formatter = logging.Formatter(DEV_FORMAT)
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Previeni la propagazione al logger root (evita duplicati)
    logger.propagate = False
    
    return logger


def configure_root_logger() -> None:
    """
    Configura il logger root dell'applicazione.
    
    Questa funzione dovrebbe essere chiamata una sola volta all'avvio
    dell'applicazione (in main.py) per configurare il logging globale.
    
    Note:
        - I logger specifici dei moduli ereditano questa configurazione
        - Puoi sovrascrivere a livello di modulo usando get_logger()
    """
    root_logger = logging.getLogger()
    
    # Evita duplicati se già configurato
    if root_logger.handlers:
        return
    
    # Livello di log per il root logger
    if DEBUG or ENVIRONMENT == "development":
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)
    
    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Formato
    if ENVIRONMENT == "production":
        formatter = logging.Formatter(PROD_FORMAT)
    else:
        formatter = logging.Formatter(DEV_FORMAT)
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


# --- LOGGER DI DEFAULT PER IL MODULO UTILS ---
logger = get_logger(__name__)

