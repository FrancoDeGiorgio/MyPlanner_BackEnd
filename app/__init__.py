"""
Pacchetto principale dell'applicazione MyPlanner Backend.

Questa è la root del nuovo layout architetturale organizzato per layer:
- api/: Presentation layer (routes, middleware, dependencies)
- services/: Business logic layer
- repositories/: Data access layer
- models/: Domain models (entità business)
- schemas/: DTO layer (Pydantic per validazione API)
- core/: Configurazione e infrastruttura centrale
- utils/: Utilities condivise
- migrations/: Database migrations (Alembic)
"""

__version__ = "2.0.0"

