"""
Pydantic Schemas (DTO - Data Transfer Objects) per autenticazione.

Questi schemi definiscono la struttura dei dati in ingresso e uscita
dalle API REST di autenticazione, con validazione automatica tramite Pydantic.

IMPORTANTE: Separazione tra Models e Schemas
---------------------------------------------
- Models (app/models/): Entità di dominio, logica di business
- Schemas (questo file): DTO per validazione input/output API

I DTO non devono mai essere usati direttamente nel dominio o repository.
Servono solo come contratto tra API e client.
"""
from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """
    Schema DTO per il token JWT restituito dopo il login.
    
    Questo è il formato standard OAuth2 per la risposta di autenticazione.
    Il client userà l'access_token negli header Authorization delle
    richieste successive come: "Authorization: Bearer <access_token>"
    
    Attributes:
        access_token: Token JWT firmato contenente i claim dell'utente
        token_type: Tipo di token, sempre "bearer" per OAuth2 Bearer tokens
    
    Example Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer"
        }
    """
    access_token: str = Field(
        ...,
        description="Token JWT per autenticazione Bearer"
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo di token OAuth2 (sempre 'bearer')"
    )


class TokenData(BaseModel):
    """
    Schema per i dati estratti e validati dal token JWT.
    
    Usato internamente dalle dependency functions (get_current_user)
    per rappresentare le informazioni decodificate dal JWT.
    
    Attributes:
        username: Username estratto dal claim 'sub' del JWT
    
    Note:
        - Questo schema NON viene esposto nelle API
        - Serve solo per type-safety nelle dependency functions
    """
    username: Optional[str] = Field(
        default=None,
        description="Username estratto dal claim 'sub' del JWT"
    )


class UserBase(BaseModel):
    """
    Schema di base per l'utente, contiene solo l'username.
    
    Usato come classe base per evitare duplicazione nei vari schema
    relativi agli utenti (registrazione, login, profilo, ecc.)
    
    Attributes:
        name_user: Username univoco dell'utente
    
    Note:
        - Validazioni aggiuntive (lunghezza, caratteri ammessi) potrebbero
          essere aggiunte con Field(min_length=..., regex=...)
    """
    name_user: str = Field(
        ...,
        description="Username univoco (usato come Subject nel JWT e tenant identifier per RLS)",
        min_length=3,
        max_length=50
    )


class UserCreate(UserBase):
    """
    Schema DTO per la registrazione di un nuovo utente.
    
    Estende UserBase aggiungendo il campo password necessario
    per la creazione di un nuovo account.
    
    Attributes:
        name_user: Ereditato da UserBase
        password: Password in chiaro fornita dall'utente (sarà hashata dal service)
    
    Example Request:
        POST /auth/register
        {
            "name_user": "mario_rossi",
            "password": "SecurePassword123!"
        }
    
    Security:
        - La password viene validata solo per lunghezza minima
        - Considerare l'aggiunta di validazioni più stringenti (lettere, numeri, simboli)
        - La password viene SEMPRE hashata dal service prima di salvare nel DB
    """
    password: str = Field(
        ...,
        description="Password dell'utente (sarà hashata prima del salvataggio)",
        min_length=6,
        max_length=100
    )


class UserResponse(UserBase):
    """
    Schema DTO per la risposta contenente informazioni utente.
    
    OPZIONALE: Attualmente non usato, ma disponibile per future API
    che restituiscono profili utente (es. GET /auth/me)
    
    Attributes:
        name_user: Username dell'utente
    
    Note:
        - NON include mai l'hashed_password (security best practice)
        - Potrebbe essere esteso con altri campi (email, created_at, ecc.)
    """
    pass  # Per ora identico a UserBase
    
    class Config:
        """Configurazione Pydantic per mapping da ORM/dict."""
        from_attributes = True  # Permette conversione da oggetti con attributi (es. dataclass)

