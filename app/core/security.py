"""
Funzioni di sicurezza: hashing password, creazione e verifica JWT.

Questo modulo centralizza tutte le operazioni di sicurezza:
- Hashing e verifica password con bcrypt
- Creazione e decodifica token JWT
- Schema OAuth2 per autenticazione Bearer

Security Best Practices implementate:
- Bcrypt per hashing password (salt automatico, configurabile cost factor)
- JWT con firma HMAC-SHA256 e scadenza configurabile
- Password mai salvate o loggate in chiaro
- Timing-safe comparison per verifica password
"""
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import jwt
from fastapi.security import OAuth2PasswordBearer

# Import della configurazione dal modulo core
from app.core.config import SECRET_KEY, ALGORITHM


# --- CONFIGURAZIONE HASHING PASSWORD ---
# Usa bcrypt come algoritmo di hashing, con deprecazione automatica
# degli schemi vecchi se necessario un aggiornamento in futuro
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# --- SCHEMA OAUTH2 ---
# Definisce lo schema di autenticazione OAuth2 Password Bearer
# Il tokenUrl indica dove il client può ottenere il token (endpoint login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str) -> str:
    """
    Genera l'hash della password usando bcrypt.
    
    Bcrypt applica automaticamente:
    - Un salt casuale univoco per ogni password
    - Molte iterazioni (configurabile tramite rounds/cost factor)
    - Protezione contro timing attacks
    
    Args:
        password: Password in chiaro da hashare
    
    Returns:
        str: Hash della password in formato bcrypt
            (include algoritmo, cost factor, salt e hash)
    
    Example:
        >>> hashed = hash_password("MySecurePassword123!")
        >>> print(hashed)
        $2b$12$KIXxLVz8r8f9GvH.../...
    
    Security Note:
        - Mai salvare la password in chiaro
        - Mai loggare la password in chiaro
        - L'hash può essere salvato nel database
        - Ogni chiamata genera un hash diverso (salt casuale)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica la corrispondenza della password in chiaro con l'hash.
    
    Confronta in modo sicuro (timing-safe) la password fornita
    con l'hash salvato nel database. Anche se l'hash contiene il salt,
    bcrypt è in grado di estrarlo e riapplicarlo per la verifica.
    
    Args:
        plain_password: Password in chiaro fornita dall'utente
        hashed_password: Hash bcrypt salvato nel database
    
    Returns:
        bool: True se la password corrisponde, False altrimenti
    
    Example:
        >>> hashed = hash_password("MyPassword")
        >>> verify_password("MyPassword", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    
    Security Note:
        - Usa constant-time comparison per prevenire timing attacks
        - Non rivela informazioni su quanto l'input sia "vicino" alla password corretta
        - Entrambi i parametri devono essere stringhe valide
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT firmato con i dati forniti.
    
    Il token JWT include:
    - Payload personalizzato (es. {"sub": "username"})
    - Timestamp di scadenza (exp claim)
    - Firma HMAC-SHA256 per integrità e autenticità
    
    Args:
        data: Dizionario con i claim da includere nel token
              Tipicamente include almeno "sub" (subject) con l'username
        expires_delta: Durata validità del token (timedelta)
                      Se None, usa 15 minuti di default
    
    Returns:
        str: Token JWT firmato, formato base64url
            (header.payload.signature)
    
    Example:
        >>> from datetime import timedelta
        >>> token = create_access_token(
        ...     data={"sub": "mario_rossi"},
        ...     expires_delta=timedelta(minutes=30)
        ... )
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYXJpb19yb3NzaSIsImV4cCI6MTYzOTU4NzYwMH0.abc123...
    
    Security Note:
        - Il token è firmato ma NON criptato: il payload è leggibile
        - Non includere dati sensibili nel payload (es. password)
        - La firma garantisce che il token non sia stato manomesso
        - SECRET_KEY deve essere robusta e mai esposta
    
    JWT Claims inclusi:
        - Custom claims: tutti i dati passati nel parametro 'data'
        - exp (expiration): timestamp di scadenza
        - (opzionale) iat (issued at): quando aggiunto automaticamente da alcune librerie
    """
    # Copia i dati per non modificare il dizionario originale
    to_encode = data.copy()
    
    # Calcola il timestamp di scadenza
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default: 15 minuti se non specificato
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    # Aggiungi il claim 'exp' (expiration time)
    # Le librerie JWT lo verificano automaticamente alla decodifica
    to_encode.update({"exp": expire})
    
    # Genera il token JWT firmato
    # jwt.encode() crea: header.payload.signature (tutto in base64url)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

