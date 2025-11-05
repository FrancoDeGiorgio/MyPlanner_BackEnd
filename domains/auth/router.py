"""
API Router per il dominio Auth (API Layer / Presentation Layer).

Definisce gli endpoint REST per autenticazione e registrazione.
Il router è responsabile SOLO di:
- Ricevere richieste HTTP
- Validare input tramite Pydantic schemas
- Delegare la business logic al Service Layer
- Restituire risposte HTTP formattate

NON contiene business logic o accesso diretto al database.
"""
import psycopg2
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from database import get_db_conn
from domains.auth.schemas import UserCreate, Token
from domains.auth.service import AuthService


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
)
def register_user(
    user: UserCreate,
    conn: psycopg2.connect = Depends(get_db_conn)
):
    """
    Endpoint per la registrazione di un nuovo utente.
    
    Processo:
    1. Riceve username e password dal client (validati da Pydantic)
    2. Delega al service la registrazione (hashing password, salvataggio DB)
    3. Restituisce conferma con l'ID del nuovo utente
    
    Args:
        user: Schema Pydantic con name_user e password
        conn: Connessione al database iniettata automaticamente
    
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
        conn=conn,
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
    form_data: OAuth2PasswordRequestForm = Depends(),
    conn: psycopg2.connect = Depends(get_db_conn)
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
        conn: Connessione al database iniettata automaticamente
    
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
        conn=conn,
        username=form_data.username,
        password=form_data.password
    )
    
    return token

