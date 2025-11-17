"""
Validatori riusabili per business logic.

Contiene funzioni di validazione che possono essere utilizzate
dai service layer per verificare regole di business complesse.

Differenza con Pydantic validators:
- Pydantic: validazione formato dati API (input/output)
- Questi: validazione regole di business (es. "la data X deve essere dopo Y")
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.core.exceptions import ValidationError


def validate_uuid(value: str, field_name: str = "ID") -> UUID:
    """
    Valida e converte una stringa in UUID.
    
    Args:
        value: Stringa da convertire in UUID
        field_name: Nome del campo (per messaggi errore)
    
    Returns:
        UUID: UUID validato
    
    Raises:
        ValidationError: Se la stringa non è un UUID valido
    
    Example:
        >>> uuid = validate_uuid("550e8400-e29b-41d4-a716-446655440000", "task_id")
        >>> print(uuid)
        UUID('550e8400-e29b-41d4-a716-446655440000')
    """
    try:
        return UUID(value)
    except (ValueError, TypeError, AttributeError) as e:
        raise ValidationError(
            message=f"{field_name} non è un UUID valido",
            details={"field": field_name, "value": value, "error": str(e)}
        )


def validate_date_range(
    start_date: datetime,
    end_date: datetime,
    start_field: str = "data_inizio",
    end_field: str = "data_fine"
) -> None:
    """
    Valida che end_date sia dopo start_date.
    
    Args:
        start_date: Data di inizio
        end_date: Data di fine
        start_field: Nome campo inizio (per messaggi errore)
        end_field: Nome campo fine (per messaggi errore)
    
    Raises:
        ValidationError: Se end_date <= start_date
    
    Example:
        >>> validate_date_range(
        ...     datetime(2025, 1, 1),
        ...     datetime(2025, 1, 10)
        ... )  # OK, nessuna eccezione
        
        >>> validate_date_range(
        ...     datetime(2025, 1, 10),
        ...     datetime(2025, 1, 1)
        ... )  # Solleva ValidationError
    """
    if end_date <= start_date:
        raise ValidationError(
            message=f"{end_field} deve essere dopo {start_field}",
            details={
                start_field: start_date.isoformat(),
                end_field: end_date.isoformat()
            }
        )


def validate_duration(
    duration_minutes: Optional[int],
    min_duration: int = 5,
    max_duration: int = 1440  # 24 ore
) -> None:
    """
    Valida che la durata in minuti sia in un range accettabile.
    
    Args:
        duration_minutes: Durata da validare (può essere None)
        min_duration: Durata minima permessa in minuti
        max_duration: Durata massima permessa in minuti
    
    Raises:
        ValidationError: Se duration_minutes è fuori range
    
    Example:
        >>> validate_duration(60)  # OK
        >>> validate_duration(2)   # ValidationError: troppo breve
        >>> validate_duration(2000)  # ValidationError: troppo lunga
    """
    if duration_minutes is None:
        return
    
    if duration_minutes < min_duration:
        raise ValidationError(
            message=f"La durata minima è {min_duration} minuti",
            details={
                "duration_minutes": duration_minutes,
                "min_duration": min_duration
            }
        )
    
    if duration_minutes > max_duration:
        raise ValidationError(
            message=f"La durata massima è {max_duration} minuti",
            details={
                "duration_minutes": duration_minutes,
                "max_duration": max_duration
            }
        )


def validate_end_time_or_duration(
    end_time: Optional[datetime],
    duration_minutes: Optional[int]
) -> None:
    """
    Valida che end_time e duration_minutes siano mutuamente esclusivi.
    
    Regola di business: una task può avere O end_time O duration_minutes,
    mai entrambi contemporaneamente.
    
    Args:
        end_time: Data/ora di fine opzionale
        duration_minutes: Durata in minuti opzionale
    
    Raises:
        ValidationError: Se entrambi sono specificati
    
    Example:
        >>> validate_end_time_or_duration(
        ...     end_time=datetime(2025, 1, 1, 15, 0),
        ...     duration_minutes=None
        ... )  # OK
        
        >>> validate_end_time_or_duration(
        ...     end_time=None,
        ...     duration_minutes=60
        ... )  # OK
        
        >>> validate_end_time_or_duration(
        ...     end_time=datetime(2025, 1, 1, 15, 0),
        ...     duration_minutes=60
        ... )  # ValidationError: entrambi specificati
    """
    if end_time is not None and duration_minutes is not None:
        raise ValidationError(
            message="Non puoi specificare sia end_time che duration_minutes",
            details={
                "end_time": end_time.isoformat(),
                "duration_minutes": duration_minutes
            }
        )


def validate_string_length(
    value: str,
    field_name: str,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> None:
    """
    Valida la lunghezza di una stringa.
    
    Args:
        value: Stringa da validare
        field_name: Nome del campo (per messaggi errore)
        min_length: Lunghezza minima opzionale
        max_length: Lunghezza massima opzionale
    
    Raises:
        ValidationError: Se la stringa è fuori range
    
    Example:
        >>> validate_string_length("Hello", "title", min_length=3, max_length=10)  # OK
        >>> validate_string_length("Hi", "title", min_length=3)  # ValidationError
    """
    actual_length = len(value)
    
    if min_length is not None and actual_length < min_length:
        raise ValidationError(
            message=f"{field_name} deve essere almeno {min_length} caratteri",
            details={
                "field": field_name,
                "actual_length": actual_length,
                "min_length": min_length
            }
        )
    
    if max_length is not None and actual_length > max_length:
        raise ValidationError(
            message=f"{field_name} non può superare {max_length} caratteri",
            details={
                "field": field_name,
                "actual_length": actual_length,
                "max_length": max_length
            }
        )


def validate_not_empty(value: str, field_name: str) -> None:
    """
    Valida che una stringa non sia vuota o composta solo da spazi.
    
    Args:
        value: Stringa da validare
        field_name: Nome del campo (per messaggi errore)
    
    Raises:
        ValidationError: Se la stringa è vuota o whitespace-only
    
    Example:
        >>> validate_not_empty("Hello", "title")  # OK
        >>> validate_not_empty("   ", "title")  # ValidationError
        >>> validate_not_empty("", "title")  # ValidationError
    """
    if not value or not value.strip():
        raise ValidationError(
            message=f"{field_name} non può essere vuoto",
            details={"field": field_name}
        )

