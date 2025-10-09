"""
Funzioni di sicurezza: hashing password, creazione e verifica JWT.
"""
from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import jwt
from fastapi.security import OAuth2PasswordBearer

from config import SECRET_KEY, ALGORITHM

# Per l'hashing delle password
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# Schema per l'autenticazione OAuth2 (per la dependency)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str):
    """Genera l'hash della password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    """Verifica la corrispondenza della password in chiaro con l'hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


