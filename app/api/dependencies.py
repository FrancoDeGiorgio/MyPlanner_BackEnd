"""
Dipendenze condivise FastAPI utilizzate dai router di tutti i domini.

Questo modulo contiene dependency injection functions che possono essere
iniettate negli endpoint FastAPI tramite il sistema Depends().
"""
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt

# Import aggiornati per la nuova architettura
from app.core.config import SECRET_KEY, ALGORITHM
from app.core.security import oauth2_scheme


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependency FastAPI per estrarre e validare l'username dal token JWT.
    
    Questa funzione viene iniettata negli endpoint protetti per:
    1. Estrarre il token Bearer dall'header Authorization
    2. Decodificare e validare il JWT usando SECRET_KEY
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
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica il JWT usando la chiave segreta e l'algoritmo configurati
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Estrae il claim 'sub' (subject) che contiene l'username
        # Questo username sarà poi usato per impostare il contesto RLS nel database
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
    except JWTError:
        # JWT malformato, scaduto o con firma invalida
        raise credentials_exception
    
    return username

