"""
Eccezioni custom dell'applicazione.

Definisce eccezioni specifiche del dominio business che possono essere
sollevate dai service/repository e gestite centralmente dai middleware.

Best Practice:
- Usare eccezioni custom per errori di business logic
- Convertire eccezioni custom in HTTPException nel middleware
- Mantenere separazione tra dominio e presentazione
"""
from typing import Optional, Any, Dict


class ApplicationError(Exception):
    """
    Classe base per tutte le eccezioni custom dell'applicazione.
    
    Attributes:
        message: Messaggio di errore leggibile
        details: Dizionario opzionale con dettagli aggiuntivi
        error_code: Codice errore custom per il client
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        """
        Inizializza un'eccezione applicativa.
        
        Args:
            message: Messaggio di errore principale
            details: Dettagli aggiuntivi opzionali (es. campi validazione)
            error_code: Codice errore machine-readable (es. "USER_NOT_FOUND")
        """
        self.message = message
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converte l'eccezione in dizionario per serializzazione JSON.
        
        Returns:
            Dict contenente messaggio, codice errore e dettagli
        """
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }


class NotFoundError(ApplicationError):
    """
    Eccezione sollevata quando una risorsa non viene trovata.
    
    Corrisponde a HTTP 404 Not Found.
    
    Example:
        >>> raise NotFoundError(
        ...     message="Task non trovata",
        ...     details={"task_id": "123e4567-e89b-12d3-a456-426614174000"}
        ... )
    """
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, error_code="NOT_FOUND")


class AlreadyExistsError(ApplicationError):
    """
    Eccezione sollevata quando si tenta di creare una risorsa già esistente.
    
    Corrisponde a HTTP 409 Conflict.
    
    Example:
        >>> raise AlreadyExistsError(
        ...     message="Username già esistente",
        ...     details={"username": "mario_rossi"}
        ... )
    """
    
    def __init__(self, message: str = "Resource already exists", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, error_code="ALREADY_EXISTS")


class ValidationError(ApplicationError):
    """
    Eccezione sollevata per errori di validazione business logic.
    
    Diversa dalla ValidationError di Pydantic (che è per input API),
    questa è per regole di business (es. "non puoi completare una task futura").
    
    Corrisponde a HTTP 422 Unprocessable Entity.
    
    Example:
        >>> raise ValidationError(
        ...     message="La data di fine deve essere dopo la data di inizio",
        ...     details={"start": "2025-01-01", "end": "2024-12-31"}
        ... )
    """
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, error_code="VALIDATION_ERROR")


class UnauthorizedError(ApplicationError):
    """
    Eccezione sollevata quando l'autenticazione fallisce.
    
    Corrisponde a HTTP 401 Unauthorized.
    
    Example:
        >>> raise UnauthorizedError(
        ...     message="Credenziali non valide"
        ... )
    """
    
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, error_code="UNAUTHORIZED")


class ForbiddenError(ApplicationError):
    """
    Eccezione sollevata quando l'utente non ha permessi per l'operazione.
    
    Corrisponde a HTTP 403 Forbidden.
    
    Differenza con UnauthorizedError:
    - 401: "non so chi sei" (manca token o è invalido)
    - 403: "so chi sei ma non puoi farlo" (non hai permessi)
    
    Example:
        >>> raise ForbiddenError(
        ...     message="Non puoi modificare task di altri utenti"
        ... )
    """
    
    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, error_code="FORBIDDEN")


class DatabaseError(ApplicationError):
    """
    Eccezione sollevata per errori database non recuperabili.
    
    Corrisponde a HTTP 500 Internal Server Error.
    
    Note:
        - Non esporre dettagli interni del database al client
        - Loggare sempre i dettagli completi per debugging
        - Usare solo per errori non gestibili (non per violazioni constraint)
    
    Example:
        >>> raise DatabaseError(
        ...     message="Errore durante il salvataggio",
        ...     details={"operation": "INSERT INTO tasks"}
        ... )
    """
    
    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, error_code="DATABASE_ERROR")


class BusinessRuleViolation(ApplicationError):
    """
    Eccezione sollevata quando una regola di business viene violata.
    
    Corrisponde a HTTP 422 Unprocessable Entity.
    
    Differenza con ValidationError:
    - ValidationError: formato dati sbagliato
    - BusinessRuleViolation: regola di business complessa violata
    
    Example:
        >>> raise BusinessRuleViolation(
        ...     message="Non puoi avere più di 100 task attive contemporaneamente",
        ...     details={"current_count": 100}
        ... )
    """
    
    def __init__(self, message: str = "Business rule violation", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details, error_code="BUSINESS_RULE_VIOLATION")

