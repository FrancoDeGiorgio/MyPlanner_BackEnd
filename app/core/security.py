"""
Funzioni di sicurezza: hashing password, creazione e verifica JWT.

Questo modulo centralizza tutte le operazioni di sicurezza:
- Hashing e verifica password con bcrypt
- Creazione e decodifica token JWT
- Schema OAuth2 per autenticazione Bearer
- Validazione password strength

Security Best Practices implementate:
- Bcrypt per hashing password (salt automatico, configurabile cost factor)
- JWT con firma HMAC-SHA256 e scadenza configurabile
- Password mai salvate o loggate in chiaro
- Timing-safe comparison per verifica password
- Password strength validation (min 8 char, maiuscole, numeri, simboli)
"""
import re
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import jwt
from fastapi.security import OAuth2PasswordBearer

# Import della configurazione dal modulo core
from app.core.config import (
    SECRET_KEY, 
    ALGORITHM, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    JWT_ISSUER,
    JWT_AUDIENCE
)


# --- CONFIGURAZIONE HASHING PASSWORD ---
# Usa bcrypt come algoritmo di hashing con cost factor esplicito
# Cost factor 12 = 2^12 = 4096 iterazioni (sicuro ma non troppo lento)
# Range consigliato: 12-14 (12 per bilanciare sicurezza/performance)
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Cost factor esplicito: 12 rounds (2^12 iterazioni)
)

# --- SCHEMA OAUTH2 ---
# Definisce lo schema di autenticazione OAuth2 Password Bearer
# Il tokenUrl indica dove il client può ottenere il token (endpoint login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Valida la complessità della password secondo criteri di sicurezza.
    
    Requisiti password:
    - Minimo 8 caratteri
    - Almeno una lettera maiuscola
    - Almeno una lettera minuscola
    - Almeno un numero
    - Almeno un carattere speciale (!@#$%^&*()_+-=[]{}|;:,.<>?)
    
    Args:
        password: Password da validare
    
    Returns:
        tuple[bool, Optional[str]]: (True, None) se valida, (False, messaggio_errore) se invalida
    
    Example:
        >>> validate_password_strength("MyPass123!")
        (True, None)
        >>> validate_password_strength("weak")
        (False, "La password deve contenere almeno 8 caratteri")
    """
    if len(password) < 8:
        return False, "La password deve contenere almeno 8 caratteri"
    
    if not re.search(r'[A-Z]', password):
        return False, "La password deve contenere almeno una lettera maiuscola"
    
    if not re.search(r'[a-z]', password):
        return False, "La password deve contenere almeno una lettera minuscola"
    
    if not re.search(r'\d', password):
        return False, "La password deve contenere almeno un numero"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, "La password deve contenere almeno un carattere speciale (!@#$%^&*()_+-=[]{}|;:,.<>?)"
    
    return True, None


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
    Crea un token JWT di accesso firmato con i dati forniti.
    
    Il token JWT include:
    - Payload personalizzato (es. {"sub": "username"})
    - Standard claims: iss, aud, exp, iat, nbf
    - Firma HMAC-SHA256 per integrità e autenticità
    
    Args:
        data: Dizionario con i claim da includere nel token
              Tipicamente include almeno "sub" (subject) con l'username
        expires_delta: Durata validità del token (timedelta)
                      Se None, usa ACCESS_TOKEN_EXPIRE_MINUTES dalla config
    
    Returns:
        str: Token JWT firmato, formato base64url
            (header.payload.signature)
    
    Example:
        >>> from datetime import timedelta
        >>> token = create_access_token(
        ...     data={"sub": "mario_rossi"},
        ...     expires_delta=timedelta(minutes=30)
        ... )
    
    Security Note:
        - Il token è firmato ma NON criptato: il payload è leggibile
        - Non includere dati sensibili nel payload (es. password)
        - La firma garantisce che il token non sia stato manomesso
        - SECRET_KEY deve essere robusta e mai esposta
    
    JWT Claims inclusi:
        - sub (subject): username dell'utente
        - iss (issuer): JWT_ISSUER dalla config
        - aud (audience): JWT_AUDIENCE dalla config
        - exp (expiration): timestamp di scadenza
        - iat (issued at): timestamp di creazione
        - nbf (not before): timestamp di validità (stesso di iat)
    """
    # Copia i dati per non modificare il dizionario originale
    to_encode = data.copy()
    
    # Timestamp corrente
    now = datetime.utcnow()
    
    # Calcola il timestamp di scadenza
    if expires_delta:
        expire = now + expires_delta
    else:
        # Default: ACCESS_TOKEN_EXPIRE_MINUTES dalla config
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Aggiungi standard JWT claims per validazione rigorosa
    to_encode.update({
        "exp": expire,                    # Expiration time
        "iat": now,                       # Issued at
        "nbf": now,                       # Not before (valido da subito)
        "iss": JWT_ISSUER,                # Issuer
        "aud": JWT_AUDIENCE,              # Audience
        "type": "access"                   # Tipo di token (per distinguere da refresh)
    })
    
    # Genera il token JWT firmato
    # jwt.encode() crea: header.payload.signature (tutto in base64url)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Crea un refresh token JWT con durata più lunga rispetto all'access token.
    
    Il refresh token viene usato per ottenere un nuovo access token senza
    richiedere nuovamente le credenziali dell'utente.
    
    Args:
        data: Dizionario con i claim da includere nel token
              Deve includere almeno "sub" (subject) con l'username
    
    Returns:
        str: Refresh token JWT firmato
    
    Security Note:
        - Refresh token ha durata più lunga (7 giorni di default)
        - Dovrebbe essere salvato in httpOnly cookie o secure storage
        - Non dovrebbe essere esposto in localStorage (più sicuro in cookie)
    """
    # Copia i dati per non modificare il dizionario originale
    to_encode = data.copy()
    
    # Timestamp corrente
    now = datetime.utcnow()
    
    # Refresh token ha durata più lunga (7 giorni di default)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Aggiungi standard JWT claims
    to_encode.update({
        "exp": expire,                    # Expiration time
        "iat": now,                       # Issued at
        "nbf": now,                       # Not before
        "iss": JWT_ISSUER,                # Issuer
        "aud": JWT_AUDIENCE,              # Audience
        "type": "refresh"                  # Tipo di token
    })
    
    # Genera il refresh token JWT firmato
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> dict:
    """
    Verifica e decodifica un token JWT con validazione completa.
    
    Valida:
    - Firma del token (HMAC-SHA256)
    - Expiration time (exp)
    - Not before (nbf)
    - Issuer (iss)
    - Audience (aud)
    - Tipo di token (type)
    
    Args:
        token: Token JWT da verificare
        token_type: Tipo di token atteso ("access" o "refresh")
    
    Returns:
        dict: Payload decodificato del token
    
    Raises:
        jwt.ExpiredSignatureError: Se il token è scaduto
        jwt.JWTClaimsError: Se i claim non sono validi (iss, aud, nbf)
        jwt.JWTError: Se il token è invalido o la firma non corrisponde
    
    Example:
        >>> payload = verify_token(token, token_type="access")
        >>> username = payload.get("sub")
    """
    try:
        # Decodifica e verifica il token con tutti i claim
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            issuer=JWT_ISSUER,
            audience=JWT_AUDIENCE,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
                "verify_nbf": True
            }
        )
        
        # Verifica che il tipo di token corrisponda
        if payload.get("type") != token_type:
            raise jwt.JWTError(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token scaduto")
    except jwt.JWTClaimsError as e:
        raise jwt.JWTClaimsError(f"Claim non validi: {str(e)}")
    except jwt.JWTError as e:
        raise jwt.JWTError(f"Token invalido: {str(e)}")

