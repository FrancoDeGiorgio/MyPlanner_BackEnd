"""
Security Headers Middleware per protezione contro attacchi comuni.

Implementa security headers standard per proteggere l'applicazione da:
- XSS (Cross-Site Scripting)
- Clickjacking
- MIME type sniffing
- Man-in-the-Middle attacks (HSTS)

Security Headers implementati:
- Content-Security-Policy (CSP): Controlla quali risorse possono essere caricate
- Strict-Transport-Security (HSTS): Forza HTTPS per N giorni
- X-Frame-Options: Previene clickjacking
- X-Content-Type-Options: Previene MIME sniffing
- X-XSS-Protection: Protezione XSS legacy (per browser vecchi)
- Referrer-Policy: Controlla informazioni referrer inviate

TODO: Implementare CSP nonce per rimuovere unsafe-inline completamente.
"""
import secrets
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.core.config import ENVIRONMENT


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware per aggiungere security headers a tutte le risposte HTTP.
    
    Applica security headers secondo le best practices OWASP e Mozilla.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Genera nonce CSP per questa richiesta (per script inline sicuri)
        # TODO: Implementare completamente nonce per rimuovere unsafe-inline
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce
        
        response = await call_next(request)
        
        # Content Security Policy
        # Permette solo risorse da self e da domini specifici
        # In produzione, aggiungere domini CDN specifici
        # TODO: Implementare nonce per script inline invece di unsafe-inline
        # Generare nonce per ogni richiesta e includerlo negli script inline
        nonce = getattr(request.state, "csp_nonce", None)
        
        if nonce:
            # CSP con nonce per script inline (più sicuro)
            csp_policy = (
                f"default-src 'self'; "
                f"script-src 'self' 'nonce-{nonce}'; "  # Nonce invece di unsafe-inline/eval
                f"style-src 'self' 'unsafe-inline'; "  # unsafe-inline per Swagger UI CSS (TODO: usare nonce anche qui)
                f"img-src 'self' data: https:; "
                f"font-src 'self' data:; "
                f"connect-src 'self'; "
                f"frame-ancestors 'none'; "  # Previene clickjacking
                f"base-uri 'self'; "
                f"form-action 'self'"
            )
        else:
            # CSP temporaneo con unsafe-inline per compatibilità (meno sicuro)
            # TODO: Rimuovere unsafe-inline dopo implementazione nonce
            csp_policy = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "  # unsafe-inline temporaneo (rimuovere dopo nonce)
                "style-src 'self' 'unsafe-inline'; "  # unsafe-inline per Swagger UI CSS
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "  # Previene clickjacking
                "base-uri 'self'; "
                "form-action 'self'"
            )
        response.headers["Content-Security-Policy"] = csp_policy
        
        # Strict Transport Security (HSTS)
        # Solo in produzione (HTTPS)
        if ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # X-Frame-Options: Previene clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options: Previene MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection: Protezione XSS per browser legacy
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy: Controlla informazioni referrer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy: Disabilita features non necessarie
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        )
        
        return response


def configure_security_headers(app: FastAPI) -> None:
    """
    Configura il middleware per security headers sull'applicazione FastAPI.
    
    Args:
        app: Istanza dell'applicazione FastAPI
    
    Security Headers applicati:
        - Content-Security-Policy: Controlla risorse caricabili
        - Strict-Transport-Security: Forza HTTPS (solo produzione)
        - X-Frame-Options: Previene clickjacking
        - X-Content-Type-Options: Previene MIME sniffing
        - X-XSS-Protection: Protezione XSS legacy
        - Referrer-Policy: Controlla informazioni referrer
        - Permissions-Policy: Disabilita features non necessarie
    
    Note:
        - CSP può essere più restrittivo in produzione
        - HSTS viene applicato solo in ambiente production
        - Alcuni header possono interferire con Swagger UI (gestito con unsafe-inline)
    """
    app.add_middleware(SecurityHeadersMiddleware)

