"""
Endpoint di autenticazione: registrazione e login.
"""
from datetime import timedelta

import psycopg2
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from config import ACCESS_TOKEN_EXPIRE_MINUTES
from database import get_db_conn
from schemas import UserCreate, Token
from security import hash_password, verify_password, create_access_token


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", summary="Registra un nuovo utente/tenant")
def register_user(user: UserCreate, conn: psycopg2.connect = Depends(get_db_conn)):
    """Crea un nuovo utente nella tabella 'users'."""
    try:
        hashed_password = hash_password(user.password)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (name_user, hashed_password) VALUES (%s, %s) RETURNING id",
                (user.name_user, hashed_password)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            return {"message": "User registered successfully", "user_id": user_id}
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {e}"
        )


@router.post("/login", response_model=Token, summary="Esegue il login e restituisce il JWT")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: psycopg2.connect = Depends(get_db_conn)
):
    """
    Verifica le credenziali e genera un token JWT.
    Il token contiene il 'name_user' nel claim 'sub', essenziale per l'RLS.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT hashed_password FROM users WHERE name_user = %s",
            (form_data.username,)
        )
        result = cur.fetchone()
        
        if result is None or not verify_password(form_data.password, result[0]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # CRITICO: Imposta 'sub' (subject) come l'username
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

