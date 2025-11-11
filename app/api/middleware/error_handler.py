"""
Gestione centralizzata degli errori per l'applicazione.

Converte eccezioni custom del dominio in risposte HTTP appropriate,
fornendo messaggi di errore consistenti e informativi.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

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
        - Logging centralizzato degli errori
        - Messaggi di errore informativi per il client
    """
    
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
        
        # Log dell'errore (in produzione usare logger strutturato)
        print(f"Application Error ({type(exc).__name__}): {exc.message}")
        
        # Restituisce risposta JSON con dettagli dell'errore
        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict()
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        Handler per eccezioni HTTP standard di Starlette/FastAPI.
        
        Formatta le eccezioni HTTP in un formato consistente con
        le altre risposte di errore dell'applicazione.
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "details": {}
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        Handler per errori di validazione Pydantic.
        
        Formatta gli errori di validazione input in modo user-friendly,
        includendo tutti i campi che hanno fallito la validazione.
        """
        # Log dell'errore
        print(f"Validation Error: {exc.errors()}")
        
        # Estrae i dettagli degli errori di validazione
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "VALIDATION_ERROR",
                "message": "Input validation failed",
                "details": {"validation_errors": errors}
            }
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """
        Handler di fallback per eccezioni non gestite.
        
        Cattura tutte le eccezioni non previste per evitare che l'applicazione
        crashe, restituendo un errore 500 generico al client.
        
        IMPORTANTE: In produzione, loggare sempre l'eccezione completa
        per debugging, ma NON esporre i dettagli interni al client.
        """
        # Log dell'errore completo (in produzione con stack trace)
        print(f"Unhandled Exception: {type(exc).__name__}: {str(exc)}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {}
            }
        )

