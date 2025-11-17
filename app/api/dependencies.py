"""
Dipendenze condivise FastAPI utilizzate dai router di tutti i domini.

Questo modulo contiene dependency injection functions che possono essere
iniettate negli endpoint FastAPI tramite il sistema Depends().
"""
from fastapi import Depends, HTTPException, status, Request
from jose import JWTError

# Import aggiornati per la nuova architettura
from app.core.security import oauth2_scheme, verify_token
from app.api.middleware.rate_limit import get_global_rate_limit


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> str:
    """
    Dependency FastAPI per estrarre e validare l'username dal token JWT.
    
    Questa funzione viene iniettata negli endpoint protetti per:
    1. Estrarre il token Bearer dall'header Authorization
    2. Decodificare e validare il JWT con validazione completa (iss, aud, exp, nbf)
    3. Estrarre il claim 'sub' (subject) che contiene l'username
    4. Restituire l'username per uso nel contesto RLS
    
    Args:
        token: Token JWT estratto automaticamente dall'header Authorization
               tramite oauth2_scheme (definito in security.py)
    
    Returns:
        str: Username dell'utente autenticato (dal claim 'sub' del JWT)
    
    Raises:
        HTTPException 401: Se il token è invalido, scaduto o mancante
    
    Example:
        @router.get("/protected")
        def protected_endpoint(username: str = Depends(get_current_user)):
            # username è ora disponibile e validato
            return {"user": username}
    
    Security:
        - Valida firma, expiration, issuer, audience, not-before
        - Verifica che il token sia di tipo "access"
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Verifica il token con validazione completa (iss, aud, exp, nbf)
        payload = verify_token(token, token_type="access")
        
        # Estrae il claim 'sub' (subject) che contiene l'username
        # Questo username sarà poi usato per impostare il contesto RLS nel database
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
    except JWTError:
        # JWT malformato, scaduto, con firma invalida o claim non validi
        raise credentials_exception
    
    return username

