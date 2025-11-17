"""
CSRF Protection Middleware per protezione contro Cross-Site Request Forgery.

Implementa il double-submit cookie pattern:
- Genera un CSRF token e lo invia sia come cookie che come header
- Valida che il token nel cookie corrisponda al token nell'header
- Protegge tutte le richieste state-changing (POST, PUT, DELETE, PATCH)
"""
import secrets
from fastapi import FastAPI, Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware per protezione CSRF usando double-submit cookie pattern.
    
    Pattern implementato:
    1. Genera CSRF token crittograficamente sicuro
    2. Invia token sia come cookie (httpOnly=False per leggibilità JS) che come header
    3. Valida che cookie e header corrispondano per richieste state-changing
    """
    
    CSRF_TOKEN_COOKIE_NAME = "XSRF-TOKEN"
    CSRF_TOKEN_HEADER_NAME = "X-XSRF-TOKEN"
    
    # Metodi HTTP che richiedono protezione CSRF
    PROTECTED_METHODS = {"POST", "PUT", "DELETE", "PATCH"}
    
    # Endpoint esenti da CSRF (es. API pubbliche, webhooks, autenticazione)
    EXEMPT_PATHS = [
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/auth/register",  # Registrazione pubblica (non autenticata)
        "/auth/login",     # Login pubblico (non autenticato)
        "/auth/refresh"    # Refresh token (usa cookie httpOnly)
    ]
    
    async def dispatch(self, request: Request, call_next):
        """
        Intercetta richieste per validazione CSRF.
        
        Per richieste state-changing:
        - Verifica presenza CSRF token nel cookie
        - Verifica presenza CSRF token nell'header
        - Valida che corrispondano
        """
        # Skip CSRF per metodi safe (GET, HEAD, OPTIONS)
        if request.method not in self.PROTECTED_METHODS:
            response = await call_next(request)
            # Genera nuovo CSRF token per ogni risposta (rotation)
            self._set_csrf_token(response, request)
            return response
        
        # Skip CSRF per endpoint esenti
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Estrai token da cookie e header
        cookie_token = request.cookies.get(self.CSRF_TOKEN_COOKIE_NAME)
        header_token = request.headers.get(self.CSRF_TOKEN_HEADER_NAME)
        
        # Per richieste state-changing, richiedi sempre il token CSRF
        # (tranne per endpoint esenti che sono già stati gestiti sopra)
        if not cookie_token and not header_token:
            # Nessun token presente: richiedi token CSRF
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token required. Please make a GET request first to obtain the token."
            )
        
        # Valida CSRF token per richieste state-changing
        # Se entrambi i token sono presenti, devono corrispondere
        if cookie_token and header_token:
            if cookie_token != header_token:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF token mismatch"
                )
        elif cookie_token or header_token:
            # Solo uno dei due presente: errore (token incompleto)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing or invalid. Both cookie and header must be present."
            )
        
        # Esegui la richiesta
        response = await call_next(request)
        
        # Imposta CSRF token nella risposta (se non presente o per rotation)
        self._set_csrf_token(response, request)
        
        return response
    
    def _generate_csrf_token(self) -> str:
        """
        Genera un CSRF token crittograficamente sicuro.
        
        Returns:
            str: Token CSRF (32 bytes hex = 64 caratteri)
        """
        return secrets.token_urlsafe(32)
    
    def _set_csrf_token(self, response: Response, request: Request):
        """
        Imposta il CSRF token come cookie nella risposta.
        
        Il token viene anche esposto nell'header per accesso JavaScript
        (necessario per double-submit cookie pattern).
        """
        # Genera nuovo token se non presente nel cookie della richiesta
        existing_token = request.cookies.get(self.CSRF_TOKEN_COOKIE_NAME)
        if not existing_token:
            token = self._generate_csrf_token()
            
            # Imposta cookie (httpOnly=False per permettere lettura JS)
            # SameSite=strict per protezione CSRF aggiuntiva
            response.set_cookie(
                key=self.CSRF_TOKEN_COOKIE_NAME,
                value=token,
                httponly=False,  # Deve essere leggibile da JavaScript per double-submit
                secure=(request.url.scheme == "https"),  # Solo HTTPS in produzione
                samesite="strict",  # Protezione CSRF
                max_age=3600,  # 1 ora
                path="/"
            )
            
            # Esponi anche nell'header per accesso JavaScript
            response.headers[self.CSRF_TOKEN_HEADER_NAME] = token


def configure_csrf_protection(app: FastAPI) -> None:
    """
    Configura il middleware CSRF sull'applicazione FastAPI.
    
    Args:
        app: Istanza dell'applicazione FastAPI
    
    Note:
        - Protegge tutte le richieste state-changing (POST, PUT, DELETE, PATCH)
        - Usa double-submit cookie pattern per compatibilità con SPA
        - Il frontend deve leggere il token dal cookie e inviarlo nell'header X-XSRF-TOKEN
    """
    app.add_middleware(CSRFProtectionMiddleware)

