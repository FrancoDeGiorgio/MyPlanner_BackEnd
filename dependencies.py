"""
Dependency functions per FastAPI endpoints.
"""
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt

from config import SECRET_KEY, ALGORITHM
from security import oauth2_scheme
from schemas import TokenData


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency per estrarre il nome utente dal JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Il claim 'sub' (subject) contiene l'username
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    return token_data.username

