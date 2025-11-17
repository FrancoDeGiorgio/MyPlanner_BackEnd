"""
API Router per autenticazione (Auth) - API Layer / Presentation Layer.

Definisce gli endpoint REST per autenticazione e registrazione.
Il router è responsabile SOLO di:
- Ricevere richieste HTTP
- Validare input tramite Pydantic schemas
- Delegare la business logic al Service Layer
- Restituire risposte HTTP formattate

NON contiene business logic o accesso diretto al database.
"""
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status, Request, Response, Body
from fastapi.security import OAuth2PasswordRequestForm

# Import aggiornati per la nuova architettura
from app.core.database import get_db
from app.schemas.auth import UserCreate, Token, RefreshTokenRequest
from app.services.auth_service import AuthService
from app.api.middleware.rate_limit import limiter, get_login_rate_limit, get_global_rate_limit
from app.core.security import verify_token, create_access_token
from app.repositories.refresh_token_repository import RefreshTokenRepository
from datetime import timedelta
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import HTTPException


# --- INIZIALIZZAZIONE ROUTER ---
# Prefix: tutti gli endpoint di questo router inizieranno con /auth
# Tags: raggruppamento nella documentazione OpenAPI
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# --- INIZIALIZZAZIONE SERVICE ---
# Il service contiene la business logic ed è usato da tutti gli endpoint
auth_service = AuthService()


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Registra un nuovo utente/tenant"
    # Rate limit gestito dal middleware globale (esente dal rate limit globale)
)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Endpoint per la registrazione di un nuovo utente.
    
    Processo:
    1. Riceve username e password dal client (validati da Pydantic)
    2. Delega al service la registrazione (hashing password, salvataggio DB)
    3. Restituisce conferma con l'ID del nuovo utente
    
    Args:
        user: Schema Pydantic con name_user e password
        db: Sessione SQLAlchemy iniettata automaticamente
    
    Returns:
        Dict: Messaggio di successo e user_id
              {"message": "User registered successfully", "user_id": "uuid..."}
    
    Raises:
        HTTPException 400: Se l'username esiste già
        HTTPException 422: Se i dati di input non sono validi (Pydantic)
        HTTPException 500: Per errori interni del server
    
    Example Request:
        POST /auth/register
        Content-Type: application/json
        
        {
            "name_user": "mario_rossi",
            "password": "SecurePass123!"
        }
    
    Example Response:
        HTTP 201 Created
        
        {
            "message": "User registered successfully",
            "user_id": "550e8400-e29b-41d4-a716-446655440000"
        }
    
    Note:
        - L'username deve essere univoco in tutto il sistema
        - La password viene automaticamente hashata dal service
        - Il nuovo utente può immediatamente fare login dopo la registrazione
    """
    # Delega tutta la logica al service
    # Il router si limita a fare da bridge tra HTTP e business logic
    result = auth_service.register_user(
        db=db,
        name_user=user.name_user,
        password=user.password
    )
    
    return result


@router.post(
    "/login",
    response_model=Token,
    summary="Esegue il login e restituisce il JWT"
)
def login_for_access_token(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint per il login e generazione del token JWT.
    
    Implementa il flusso OAuth2 Password Flow:
    1. Riceve username e password tramite form data (standard OAuth2)
    2. Delega al service la verifica delle credenziali
    3. Restituisce il token JWT se le credenziali sono corrette
    
    Args:
        form_data: Form OAuth2 con username e password
                   (Content-Type: application/x-www-form-urlencoded)
        db: Sessione SQLAlchemy iniettata automaticamente
    
    Returns:
        Token: Oggetto con access_token e token_type
               {"access_token": "eyJ...", "token_type": "bearer"}
    
    Raises:
        HTTPException 401: Se username o password sono errati
        HTTPException 500: Per errori interni del server
    
    Example Request:
        POST /auth/login
        Content-Type: application/x-www-form-urlencoded
        
        username=mario_rossi&password=SecurePass123!
    
    Example Response:
        HTTP 200 OK
        
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtYXJpb19yb3NzaSIsImV4cCI6MTYzOTU4NzYwMH0.abc123...",
            "token_type": "bearer"
        }
    
    Usage:
        Dopo aver ottenuto il token, il client deve includerlo in tutte
        le richieste successive agli endpoint protetti:
        
        Authorization: Bearer <access_token>
    
    Note:
        - Usa OAuth2PasswordRequestForm per compatibilità con standard OAuth2
        - Il token contiene il claim 'sub' con l'username (usato per RLS)
        - Il token ha una scadenza configurabile (default 30 minuti)
        - Per sicurezza, l'errore è generico sia per username che password errati
    """
    # Delega tutta la logica di autenticazione al service
    # Il service verifica le credenziali e genera il JWT
    token = auth_service.authenticate_user(
        db=db,
        username=form_data.username,
        password=form_data.password
    )
    
    # Imposta refresh token in httpOnly cookie per protezione XSS
    # Access token rimane in JSON response (deve essere leggibile dal client per Authorization header)
    response.set_cookie(
        key="refresh_token",
        value=token["refresh_token"],
        httponly=True,  # Non accessibile via JavaScript (protezione XSS)
        secure=True,  # Solo HTTPS (in produzione)
        samesite="strict",  # Protezione CSRF
        max_age=7 * 24 * 60 * 60,  # 7 giorni (in secondi)
        path="/auth"  # Disponibile solo su /auth/* endpoints
    )
    
    # Restituisce solo access token (refresh token è nel cookie)
    return {
        "access_token": token["access_token"],
        "refresh_token": token["refresh_token"],  # Manteniamo per retrocompatibilità, ma preferire cookie
        "token_type": token["token_type"]
    }


@router.post(
    "/refresh",
    response_model=Token,
    summary="Rinnova l'access token usando il refresh token"
)
def refresh_access_token(
    request: Request,
    response: Response,
    refresh_request: Optional[RefreshTokenRequest] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint per rinnovare l'access token usando un refresh token valido.
    
    Implementa il flusso OAuth2 Refresh Token Flow con token rotation:
    1. Riceve un refresh token valido
    2. Verifica che il refresh token sia valido, non scaduto e non revocato (blacklist)
    3. Revoca il vecchio refresh token (rotation)
    4. Genera un nuovo access token e un nuovo refresh token
    5. Restituisce i nuovi token
    
    Args:
        refresh_request: Schema con refresh_token
        db: Sessione SQLAlchemy (iniettata automaticamente)
    
    Returns:
        Token: Oggetto con nuovo access_token, refresh_token e token_type
    
    Raises:
        HTTPException 401: Se il refresh token è invalido, scaduto o revocato
        HTTPException 500: Per errori interni del server
    
    Example Request:
        POST /auth/refresh
        Content-Type: application/json
        
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    
    Example Response:
        HTTP 200 OK
        
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
    
    Security:
        - Valida che il refresh token sia di tipo "refresh"
        - Verifica tutti i claim (iss, aud, exp, nbf)
        - Verifica che il token non sia revocato (blacklist)
        - Implementa token rotation (ogni refresh genera nuovo token)
        - Genera un nuovo access token con durata breve
    """
    refresh_token_repo = RefreshTokenRepository()
    
    # Preferisce refresh token dal cookie httpOnly, fallback a body per retrocompatibilità
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token and refresh_request:
        refresh_token = refresh_request.refresh_token
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # STEP 1: Verifica che il token sia valido nel database (non revocato, non scaduto)
        if not refresh_token_repo.is_token_valid(db, refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or revoked refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # STEP 2: Verifica il refresh token con validazione completa (JWT claims)
        payload = verify_token(refresh_token, token_type="refresh")
        
        # STEP 3: Estrae l'username dal claim 'sub'
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # STEP 4: Recupera l'utente per ottenere l'ID
        from app.repositories.user_repository import UserRepository
        user_repo = UserRepository()
        user = user_repo.get_user_by_username(db, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # STEP 5: Genera un nuovo access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": username},
            expires_delta=access_token_expires
        )
        
        # STEP 6: Genera un nuovo refresh token (rotation)
        from app.core.security import create_refresh_token
        new_refresh_token = create_refresh_token(data={"sub": username})
        
        # STEP 7: Implementa token rotation (revoca vecchio, crea nuovo)
        refresh_token_repo.rotate_token(
            db=db,
            old_token=refresh_token,
            new_token=new_refresh_token,
            user_id=user.id
        )
        
        # Imposta nuovo refresh token in httpOnly cookie
        from app.core.config import ENVIRONMENT
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=(ENVIRONMENT == "production"),  # Solo HTTPS in produzione
            samesite="strict",
            max_age=7 * 24 * 60 * 60,
            path="/auth"
        )
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,  # Manteniamo per retrocompatibilità
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Token invalido, scaduto o con claim non validi
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

