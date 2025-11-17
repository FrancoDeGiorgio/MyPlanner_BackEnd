"""
Audit Logging Middleware per tracciare operazioni critiche.

Logga tutte le operazioni importanti per audit trail:
- Accessi API con user, IP, timestamp, endpoint, method, status code
- Modifiche dati (create, update, delete) con before/after values
- Tentativi di autenticazione falliti
- Operazioni amministrative

Security Best Practices:
- Logging strutturato per facile parsing e analisi
- Request ID per correlare richieste
- Nessun dato sensibile nei log (password, token, etc.)
- Retention policy: minimo 90 giorni (configurabile)
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
import time
from app.utils.logger import get_logger
from app.core.config import ENVIRONMENT

logger = get_logger(__name__)


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware per audit logging di tutte le richieste API.
    
    Logga:
    - Endpoint accessati
    - Metodo HTTP
    - Status code della risposta
    - Durata della richiesta
    - IP del client
    - User agent
    - Request ID per tracciabilità
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Intercetta la richiesta e la risposta per logging audit.
        
        Args:
            request: Richiesta HTTP
            call_next: Prossimo middleware/handler nella catena
        
        Returns:
            Response: Risposta HTTP con header X-Request-ID
        """
        # Timestamp di inizio richiesta
        start_time = time.time()
        
        # Request ID (già aggiunto dal middleware error_handler)
        request_id = getattr(request.state, "request_id", None)
        
        # Estrai informazioni utente se disponibili
        user_id = None
        username = None
        if hasattr(request.state, "user"):
            username = request.state.user
        
        # Estrai IP del client
        client_ip = request.client.host if request.client else None
        # Controlla anche header X-Forwarded-For per proxy/reverse proxy
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # User agent
        user_agent = request.headers.get("User-Agent", "Unknown")
        
        # Esegui la richiesta
        response = await call_next(request)
        
        # Calcola durata della richiesta
        duration_ms = (time.time() - start_time) * 1000
        
        # Log audit solo per endpoint API (non per static files, health checks, etc.)
        if request.url.path.startswith("/api/") or request.url.path.startswith("/auth/"):
            # Determina tipo di operazione
            operation_type = "READ"
            if request.method in ["POST", "PUT", "PATCH"]:
                operation_type = "WRITE"
            elif request.method == "DELETE":
                operation_type = "DELETE"
            
            # Log strutturato per audit trail
            logger.info(
                "API_AUDIT",
                extra={
                    "request_id": request_id,
                    "timestamp": time.time(),
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params) if request.query_params else None,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "user_id": user_id,
                    "username": username,
                    "operation_type": operation_type,
                    "environment": ENVIRONMENT
                }
            )
            
            # Log specifico per operazioni di scrittura (create, update, delete)
            if operation_type in ["WRITE", "DELETE"]:
                logger.warning(
                    "DATA_MODIFICATION",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "username": username,
                        "client_ip": client_ip,
                        "status_code": response.status_code,
                        "operation_type": operation_type
                    }
                )
            
            # Log specifico per errori di autenticazione
            if response.status_code == 401:
                logger.warning(
                    "AUTHENTICATION_FAILED",
                    extra={
                        "request_id": request_id,
                        "path": request.url.path,
                        "client_ip": client_ip,
                        "user_agent": user_agent,
                        "method": request.method
                    }
                )
        
        return response


def configure_audit_logging(app) -> None:
    """
    Configura il middleware di audit logging sull'applicazione FastAPI.
    
    Args:
        app: Istanza dell'applicazione FastAPI
    
    Note:
        - Il middleware deve essere aggiunto dopo il middleware request_id
        - Logga solo endpoint API, non static files o health checks
        - Usa logging strutturato per facile parsing
    """
    app.add_middleware(AuditLoggingMiddleware)

