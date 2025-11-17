"""
Gestione centralizzata degli errori per l'applicazione.

Converte eccezioni custom del dominio in risposte HTTP appropriate,
fornendo messaggi di errore consistenti e informativi.

Security Best Practices:
- Nasconde stack trace in produzione
- Logging strutturato per audit trail
- Request ID per tracciabilità
"""
import uuid
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Import delle eccezioni custom
from app.core.exceptions import (
    ApplicationError,
    NotFoundError,
    AlreadyExistsError,
    ValidationError,
    UnauthorizedError,
    ForbiddenError,
    DatabaseError,
    BusinessRuleViolation
)
from app.core.config import ENVIRONMENT, DEBUG
from app.utils.logger import get_logger

logger = get_logger(__name__)


def configure_error_handlers(app: FastAPI) -> None:
    """
    Configura gli exception handler custom sull'applicazione FastAPI.
    
    Registra handler per:
    - Eccezioni custom dell'applicazione (ApplicationError e sottoclassi)
    - Eccezioni HTTP di Starlette
    - Errori di validazione Pydantic
    - Eccezioni generiche non gestite
    
    Args:
        app: Istanza dell'applicazione FastAPI
    
    Benefits:
        - Risposte di errore consistenti in tutta l'applicazione
        - Separazione tra errori di dominio e rappresentazione HTTP
        - Logging strutturato degli errori
        - Messaggi di errore informativi per il client
        - Nasconde stack trace in produzione (security best practice)
        - Request ID per tracciabilità
    """
    
    # Middleware per aggiungere request ID a ogni richiesta
    @app.middleware("http")
    async def add_request_id_middleware(request: Request, call_next):
        """Aggiunge un request ID univoco a ogni richiesta per tracciabilità."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    
    @app.exception_handler(ApplicationError)
    async def application_error_handler(request: Request, exc: ApplicationError):
        """
        Handler per tutte le eccezioni custom dell'applicazione.
        
        Converte le eccezioni di dominio in risposte HTTP appropriate
        basandosi sul tipo di eccezione.
        """
        # Mappa il tipo di eccezione allo status code HTTP
        status_code_map = {
            NotFoundError: status.HTTP_404_NOT_FOUND,
            AlreadyExistsError: status.HTTP_409_CONFLICT,
            ValidationError: status.HTTP_422_UNPROCESSABLE_ENTITY,
            UnauthorizedError: status.HTTP_401_UNAUTHORIZED,
            ForbiddenError: status.HTTP_403_FORBIDDEN,
            DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
            BusinessRuleViolation: status.HTTP_422_UNPROCESSABLE_ENTITY,
        }
        
        # Determina lo status code appropriato
        status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Request ID per tracciabilità
        request_id = getattr(request.state, "request_id", None)
        
        # Log strutturato dell'errore
        logger.error(
            "Application Error",
            extra={
                "error_type": type(exc).__name__,
                "error_message": exc.message,
                "status_code": status_code,
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "user": getattr(request.state, "user", None)
            }
        )
        
        # Prepara risposta con request ID
        error_response = exc.to_dict()
        if request_id:
            error_response["request_id"] = request_id
        
        # Restituisce risposta JSON con dettagli dell'errore
        response = JSONResponse(
            status_code=status_code,
            content=error_response
        )
        if request_id:
            response.headers["X-Request-ID"] = request_id
        return response
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Handler per eccezioni HTTP standard di Starlette/FastAPI.
        
        Formatta le eccezioni HTTP in un formato consistente con
        le altre risposte di errore dell'applicazione.
        """
        request_id = getattr(request.state, "request_id", None)
        
        # Log dell'errore HTTP
        logger.warning(
            "HTTP Exception",
            extra={
                "status_code": exc.status_code,
                "detail": exc.detail,
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        error_response = {
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": {}
        }
        if request_id:
            error_response["request_id"] = request_id
        
        response = JSONResponse(
            status_code=exc.status_code,
            content=error_response
        )
        if request_id:
            response.headers["X-Request-ID"] = request_id
        return response
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handler per errori di validazione Pydantic.
        
        Formatta gli errori di validazione input in modo user-friendly,
        includendo tutti i campi che hanno fallito la validazione.
        """
        request_id = getattr(request.state, "request_id", None)
        
        # Estrae i dettagli degli errori di validazione
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        # Log dell'errore di validazione
        logger.warning(
            "Validation Error",
            extra={
                "errors": errors,
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method
            }
        )
        
        error_response = {
            "error": "VALIDATION_ERROR",
            "message": "Input validation failed",
            "details": {"validation_errors": errors}
        }
        if request_id:
            error_response["request_id"] = request_id
        
        response = JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response
        )
        if request_id:
            response.headers["X-Request-ID"] = request_id
        return response
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """
        Handler di fallback per eccezioni non gestite.
        
        Cattura tutte le eccezioni non previste per evitare che l'applicazione
        crashe, restituendo un errore 500 generico al client.
        
        IMPORTANTE: In produzione, loggare sempre l'eccezione completa
        per debugging, ma NON esporre i dettagli interni al client.
        """
        request_id = getattr(request.state, "request_id", None)
        
        # Importa traceback per logging completo
        import traceback
        
        # Log completo dell'errore (sempre con stack trace per debugging)
        logger.error(
            "Unhandled Exception",
            extra={
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "stack_trace": traceback.format_exc() if DEBUG or ENVIRONMENT != "production" else None
            },
            exc_info=True  # Include stack trace nel log
        )
        
        # Prepara risposta di errore
        # In produzione, nascondi dettagli interni (security best practice)
        error_response = {
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {}
        }
        
        # In development, include più dettagli per debugging
        if DEBUG or ENVIRONMENT != "production":
            error_response["details"] = {
                "error_type": type(exc).__name__,
                "error_message": str(exc)
            }
        
        if request_id:
            error_response["request_id"] = request_id
        
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )
        if request_id:
            response.headers["X-Request-ID"] = request_id
        return response

